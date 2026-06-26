# JWT Secret Centralization Checkpoint (2026-06-26)

## Scope completed

- Centralized JWT secret resolution to settings as the single source of truth.
- Removed environment-variable reads from JWT utility paths.
- Enforced production/staging secret quality validation for JWT and signed URL secrets.
- Added explicit precedence rules and regression coverage for legacy compatibility.
- Verified token rotation behavior invalidates old sessions.

## Secret precedence

- JWT secret resolution:
  - TECH_RESTORE_JWT_SECRET
  - SECRET_KEY (legacy alias)
  - development fallback (development only)

- Signed URL secret resolution:
  - TECH_RESTORE_SIGNED_URL_SECRET
  - TECH_RESTORE_JWT_SECRET
  - SECRET_KEY (legacy alias)
  - development fallback (development only)

## Production/staging validation

Startup now rejects:

- Missing or development-default JWT/signed secrets.
- Obvious placeholder values.
- Secrets below minimum length threshold.

## Rotation implications

- Rotating TECH_RESTORE_JWT_SECRET invalidates existing bearer sessions immediately.
- All users must log in again after JWT secret rotation.

## Verification summary

- Targeted Stage 1 auth/settings/JWT tests: pass.
- Full backend test suite: pass.
- Full frontend test suite: pass.
- Frontend build: pass.
- Startup smoke under valid production-like configuration: pass.
- Startup failure under invalid production secret configuration: pass.
