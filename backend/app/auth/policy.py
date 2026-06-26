from __future__ import annotations

from collections.abc import Iterable


ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_TECHNICIAN = "technician"
ROLE_FRONT_DESK = "front_desk"
ROLE_VIEWER = "viewer"

ALL_ROLES = {
    ROLE_OWNER,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_TECHNICIAN,
    ROLE_FRONT_DESK,
    ROLE_VIEWER,
}

INVITABLE_ROLES_BY_ACTOR: dict[str, set[str]] = {
    ROLE_OWNER: {
        ROLE_VIEWER,
        ROLE_FRONT_DESK,
        ROLE_TECHNICIAN,
        ROLE_MANAGER,
        ROLE_ADMIN,
        ROLE_OWNER,
    },
    ROLE_ADMIN: {
        ROLE_VIEWER,
        ROLE_FRONT_DESK,
        ROLE_TECHNICIAN,
    },
}


def _normalized_role(role: str | None) -> str:
    return (role or "").strip().lower()


def invitable_roles_for(actor_role: str | None) -> set[str]:
    return set(INVITABLE_ROLES_BY_ACTOR.get(_normalized_role(actor_role), set()))


def can_invite_role(actor_role: str | None, target_role: str | None) -> bool:
    normalized_target = _normalized_role(target_role)
    if normalized_target not in ALL_ROLES:
        return False
    return normalized_target in invitable_roles_for(actor_role)


def can_manage_invite(actor: dict | None, invite: dict | None) -> bool:
    if not actor or not invite:
        return False
    return can_invite_role(actor.get("role"), invite.get("role"))


def filter_visible_invites(actor: dict | None, invites: Iterable[dict]) -> list[dict]:
    return [invite for invite in invites if can_manage_invite(actor, invite)]


def can_manage_user(actor: dict | None, _target_user: dict | None = None) -> bool:
    if not actor:
        return False
    return _normalized_role(actor.get("role")) == ROLE_OWNER


def can_change_role(actor: dict | None, _target_user: dict | None, new_role: str | None) -> bool:
    if not can_manage_user(actor, _target_user):
        return False
    return _normalized_role(new_role) in ALL_ROLES
