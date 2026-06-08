from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import require_role
from market_updates.allowlist import (
    approve_invite_request,
    create_or_update_invite_request,
    deny_invite_request,
    disable_allowlist_number,
    list_allowlist,
    list_invite_requests,
    upsert_allowlist_number,
)
from market_updates.feedback_store import list_feedback_entries

router = APIRouter(prefix="/api/market-updates/admin", tags=["market-updates-admin"])


class AllowlistUpsertRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=32)
    label: str | None = None
    enabled: bool = True


class InviteDraftRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=32)
    requested_label: str | None = None
    message_text: str | None = None


@router.get("/allowlist")
def get_allowlist(_: dict = Depends(require_role("admin"))) -> list[dict]:
    return list_allowlist()


@router.post("/allowlist")
def post_allowlist(payload: AllowlistUpsertRequest, _: dict = Depends(require_role("admin"))) -> dict:
    try:
        return upsert_allowlist_number(payload.phone_number, label=payload.label, enabled=payload.enabled)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/allowlist/{phone_number}")
def delete_allowlist(phone_number: str, _: dict = Depends(require_role("admin"))) -> dict:
    removed = disable_allowlist_number(phone_number)
    return {"removed": removed}


@router.get("/invite-requests")
def get_invite_requests(status: str = "pending", _: dict = Depends(require_role("admin"))) -> list[dict]:
    return list_invite_requests(status=status)


@router.post("/invite-requests")
def post_invite_request(payload: InviteDraftRequest, _: dict = Depends(require_role("admin"))) -> dict:
    try:
        return create_or_update_invite_request(
            payload.phone_number,
            message_text=payload.message_text,
            requested_label=payload.requested_label,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/invite-requests/{request_id}/approve")
def post_approve_request(request_id: int, _: dict = Depends(require_role("admin"))) -> dict:
    approved = approve_invite_request(request_id)
    if approved is None:
        raise HTTPException(status_code=404, detail="Invite request not found")
    return approved


@router.post("/invite-requests/{request_id}/deny")
def post_deny_request(request_id: int, _: dict = Depends(require_role("admin"))) -> dict:
    denied = deny_invite_request(request_id)
    if denied is None:
        raise HTTPException(status_code=404, detail="Invite request not found")
    return denied


@router.get("/feedback")
def get_feedback(limit: int = 200, _: dict = Depends(require_role("admin"))) -> list[dict]:
    return list_feedback_entries(limit=limit)
