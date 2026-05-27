from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt

from app.core.settings import get_settings
from app.repositories.attachments import AttachmentRepository
from app.repositories.ticket import TicketRepository
from app.services.audit import AuditService
from app.storage.providers import StorageObject, build_storage_provider

ATTACHMENT_TYPES = {
    "intake_photo",
    "repair_evidence",
    "customer_signature",
    "receipt",
    "invoice",
    "donor_device_photo",
    "warranty_documentation",
}

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
DOCUMENT_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

TYPE_ALLOWED_MIME_TYPES = {
    "intake_photo": IMAGE_MIME_TYPES,
    "repair_evidence": IMAGE_MIME_TYPES,
    "customer_signature": IMAGE_MIME_TYPES,
    "donor_device_photo": IMAGE_MIME_TYPES,
    "receipt": DOCUMENT_MIME_TYPES,
    "invoice": DOCUMENT_MIME_TYPES,
    "warranty_documentation": DOCUMENT_MIME_TYPES,
}


@dataclass(frozen=True)
class SignedDownload:
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class DownloadPayload:
    attachment: dict
    object_data: StorageObject


class AttachmentService:
    @staticmethod
    def _build_storage_key(*, entity_type: str, entity_id: int, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        safe_suffix = suffix if suffix and len(suffix) <= 10 else ""
        return f"{entity_type}/{entity_id}/{datetime.now(UTC).strftime('%Y/%m/%d')}/{uuid4().hex}{safe_suffix}"

    @staticmethod
    def _sniff_mime(content: bytes, filename: str) -> str:
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if content[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"

        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed
        return "application/octet-stream"

    @staticmethod
    def _validate_entity_link(entity_type: str, entity_id: int) -> None:
        if entity_type == "ticket":
            if TicketRepository.get(entity_id) is None:
                raise ValueError("Linked ticket not found")
            return
        raise ValueError("Unsupported entity type")

    @staticmethod
    def _effective_mime_type(filename: str, client_mime: str | None, content: bytes) -> str:
        sniffed = AttachmentService._sniff_mime(content, filename)
        if sniffed != "application/octet-stream":
            return sniffed
        if client_mime:
            return client_mime.lower().strip()
        return sniffed

    @staticmethod
    def upload_attachment(
        *,
        attachment_type: str,
        entity_type: str,
        entity_id: int,
        original_filename: str,
        client_mime_type: str | None,
        content: bytes,
        uploaded_by: int | None,
    ) -> dict:
        settings = get_settings()
        provider = build_storage_provider(settings)

        if attachment_type not in ATTACHMENT_TYPES:
            raise ValueError("Unsupported attachment type")
        if not original_filename:
            raise ValueError("File name is required")
        if not content:
            raise ValueError("Attachment file is empty")
        if len(content) > settings.attachments_max_file_size_bytes:
            raise ValueError("Attachment exceeds maximum upload size")

        AttachmentService._validate_entity_link(entity_type, entity_id)

        mime_type = AttachmentService._effective_mime_type(original_filename, client_mime_type, content)
        if mime_type not in settings.attachments_allowed_mime_types:
            raise ValueError("Unsupported MIME type")

        allowed_for_type = TYPE_ALLOWED_MIME_TYPES.get(attachment_type, set())
        if mime_type not in allowed_for_type:
            raise ValueError("MIME type is not allowed for this attachment type")

        storage_key = AttachmentService._build_storage_key(
            entity_type=entity_type,
            entity_id=entity_id,
            filename=original_filename,
        )
        provider.put_object(key=storage_key, content=content, content_type=mime_type)

        item = AttachmentRepository.create(
            attachment_type=attachment_type,
            entity_type=entity_type,
            entity_id=entity_id,
            storage_key=storage_key,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=len(content),
            uploaded_by=uploaded_by,
        )

        AuditService.log(
            entity_type="attachment",
            entity_id=item["id"],
            action="attachment_uploaded",
            new_value={
                "attachment_type": attachment_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "mime_type": mime_type,
                "file_size": len(content),
            },
        )
        return item

    @staticmethod
    def list_attachments(*, entity_type: str, entity_id: int) -> list[dict]:
        AttachmentService._validate_entity_link(entity_type, entity_id)
        return AttachmentRepository.list_for_entity(entity_type=entity_type, entity_id=entity_id)

    @staticmethod
    def generate_signed_download(*, attachment_id: int, requested_by: dict) -> SignedDownload:
        settings = get_settings()
        attachment = AttachmentRepository.get(attachment_id)
        if attachment is None:
            raise ValueError("Attachment not found")

        uid = requested_by.get("id")
        if not isinstance(uid, int):
            raise ValueError("Invalid requester")

        expires_at = datetime.now(UTC) + timedelta(seconds=settings.attachments_signed_url_ttl_seconds)
        payload = {
            "aid": attachment_id,
            "uid": uid,
            "act": "attachment_download",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, settings.signed_url_secret, algorithm="HS256")
        return SignedDownload(token=token, expires_at=expires_at)

    @staticmethod
    def resolve_download_token(*, token: str, requested_by: dict) -> DownloadPayload:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.signed_url_secret, algorithms=["HS256"])
        except Exception as error:
            raise ValueError("Invalid or expired download token") from error

        attachment_id = payload.get("aid")
        token_user_id = payload.get("uid")
        if not isinstance(attachment_id, int) or not isinstance(token_user_id, int):
            raise ValueError("Invalid download token payload")

        requester_id = requested_by.get("id")
        requester_role = requested_by.get("role")
        if not isinstance(requester_id, int):
            raise ValueError("Invalid requester")

        if requester_id != token_user_id and requester_role != "admin":
            raise ValueError("Download token does not match current user")

        attachment = AttachmentRepository.get(attachment_id)
        if attachment is None:
            raise ValueError("Attachment not found")

        provider = build_storage_provider(settings)
        object_data = provider.get_object(key=attachment["storage_key"])

        AuditService.log(
            entity_type="attachment",
            entity_id=attachment_id,
            action="attachment_downloaded",
            new_value={
                "entity_type": attachment.get("entity_type"),
                "entity_id": attachment.get("entity_id"),
            },
        )

        return DownloadPayload(attachment=attachment, object_data=object_data)

    @staticmethod
    def delete_attachment(*, attachment_id: int, deleted_by: dict) -> dict:
        settings = get_settings()
        provider = build_storage_provider(settings)

        existing = AttachmentRepository.get(attachment_id)
        if existing is None:
            raise ValueError("Attachment not found")

        provider.delete_object(key=existing["storage_key"])
        deleted = AttachmentRepository.delete(attachment_id)
        if deleted is None:
            raise ValueError("Attachment not found")

        AuditService.log(
            entity_type="attachment",
            entity_id=attachment_id,
            action="attachment_deleted",
            old_value={
                "storage_key": existing["storage_key"],
                "entity_type": existing["entity_type"],
                "entity_id": existing["entity_id"],
            },
            new_value={"deleted_by": deleted_by.get("id")},
        )
        return deleted

    @staticmethod
    def cleanup_orphans(*, prefix: str = "") -> dict:
        settings = get_settings()
        provider = build_storage_provider(settings)

        metadata_keys = set(AttachmentRepository.list_storage_keys())
        stored_keys = provider.iter_keys(prefix=prefix)

        orphan_keys = [key for key in stored_keys if key not in metadata_keys]
        deleted_count = 0
        for key in orphan_keys:
            provider.delete_object(key=key)
            deleted_count += 1

        AuditService.log(
            entity_type="attachment",
            action="attachment_orphan_cleanup",
            new_value={
                "prefix": prefix,
                "deleted_count": deleted_count,
            },
        )

        return {
            "deleted_count": deleted_count,
            "deleted_keys": orphan_keys,
        }
