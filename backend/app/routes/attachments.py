from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.auth.dependencies import get_current_user, require_role
from app.models import (
    AttachmentCleanupResponse,
    AttachmentResponse,
    AttachmentSignedUrlResponse,
)
from app.services.attachments import AttachmentService

router = APIRouter(prefix="/api", tags=["attachments"])


@router.post(
    "/tickets/{ticket_id}/attachments",
    response_model=AttachmentResponse,
    status_code=201,
)
async def post_ticket_attachment(
    ticket_id: int,
    attachment_type: str = Query(...),
    file: UploadFile = File(...),
    user: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> AttachmentResponse:
    try:
        content = await file.read()
        item = AttachmentService.upload_attachment(
            attachment_type=attachment_type,
            entity_type="ticket",
            entity_id=ticket_id,
            original_filename=file.filename or "upload.bin",
            client_mime_type=file.content_type,
            content=content,
            uploaded_by=user.get("id") if isinstance(user.get("id"), int) else None,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AttachmentResponse.model_validate(item)


@router.get("/tickets/{ticket_id}/attachments", response_model=list[AttachmentResponse])
def get_ticket_attachments(
    ticket_id: int,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> list[AttachmentResponse]:
    try:
        rows = AttachmentService.list_attachments(entity_type="ticket", entity_id=ticket_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [AttachmentResponse.model_validate(item) for item in rows]


@router.post("/attachments/{attachment_id}/signed-url", response_model=AttachmentSignedUrlResponse)
def post_attachment_signed_url(
    attachment_id: int,
    user: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> AttachmentSignedUrlResponse:
    try:
        signed = AttachmentService.generate_signed_download(attachment_id=attachment_id, requested_by=user)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return AttachmentSignedUrlResponse(
        url=f"/api/attachments/download/{signed.token}",
        expires_at=signed.expires_at.isoformat(),
    )


@router.get("/attachments/download/{token}")
def get_attachment_download(
    token: str,
    user: dict = Depends(get_current_user),
) -> Response:
    try:
        payload = AttachmentService.resolve_download_token(token=token, requested_by=user)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    attachment = payload.attachment
    filename = quote(str(attachment["original_filename"]))
    content_type = str(attachment["mime_type"])

    return Response(
        content=payload.object_data.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "X-Attachment-Id": str(attachment["id"]),
        },
    )


@router.delete("/attachments/{attachment_id}", response_model=AttachmentResponse)
def delete_attachment(
    attachment_id: int,
    user: dict = Depends(require_role("admin", "front_desk")),
) -> AttachmentResponse:
    try:
        deleted = AttachmentService.delete_attachment(attachment_id=attachment_id, deleted_by=user)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return AttachmentResponse.model_validate(deleted)


@router.post("/attachments/cleanup-orphans", response_model=AttachmentCleanupResponse)
def post_attachment_cleanup_orphans(
    prefix: str = Query(default=""),
    _: dict = Depends(require_role("admin")),
) -> AttachmentCleanupResponse:
    report = AttachmentService.cleanup_orphans(prefix=prefix)
    return AttachmentCleanupResponse.model_validate(report)
