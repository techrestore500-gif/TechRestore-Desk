from __future__ import annotations

from app.database import (
    create_attachment_metadata,
    delete_attachment_metadata,
    get_attachment_metadata,
    list_attachment_storage_keys,
    list_attachments_for_entity,
)


class AttachmentRepository:
    @staticmethod
    def create(
        *,
        attachment_type: str,
        entity_type: str,
        entity_id: int,
        storage_key: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        uploaded_by: int | None,
    ) -> dict:
        return create_attachment_metadata(
            attachment_type=attachment_type,
            entity_type=entity_type,
            entity_id=entity_id,
            storage_key=storage_key,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
        )

    @staticmethod
    def get(attachment_id: int) -> dict | None:
        return get_attachment_metadata(attachment_id)

    @staticmethod
    def list_for_entity(entity_type: str, entity_id: int) -> list[dict]:
        return list_attachments_for_entity(entity_type=entity_type, entity_id=entity_id)

    @staticmethod
    def delete(attachment_id: int) -> dict | None:
        return delete_attachment_metadata(attachment_id)

    @staticmethod
    def list_storage_keys() -> list[str]:
        return list_attachment_storage_keys()
