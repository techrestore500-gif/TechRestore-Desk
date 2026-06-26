# 2026-06-26 JWT Secret Centralization Checkpoint

## Delivered

- JWT encode/decode paths now resolve secrets via centralized settings only.
- Production/staging startup blocks weak, placeholder, default, or missing secrets.
- Secret precedence and legacy SECRET_KEY compatibility are explicitly tested.
- Session invalidation after JWT secret rotation is verified.
- Invite token flow remains functional after JWT rotation.

## Validation

- Backend full test suite: pass.
- Frontend full test suite: pass.
- Frontend build: pass.
- Production-like startup smoke: pass.
- Invalid production secret startup block: pass.

## Operational note

After rotating TECH_RESTORE_JWT_SECRET, active sessions become invalid and users must sign in again.
