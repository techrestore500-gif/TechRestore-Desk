# Gate 9 + Gate 10 Execution Notes

## Gate 9: File Storage + Attachment Infrastructure

### Implemented Architecture

- Attachment metadata table added to SQLite (`attachments`) with no blob storage.
- Object storage abstraction introduced with two providers:
  - local filesystem provider for development
  - S3-compatible provider for R2/S3-style deployments
- Service layer (`AttachmentService`) owns:
  - MIME and size validation
  - attachment linking validation
  - storage coordination
  - metadata persistence
  - signed download token generation
  - orphan cleanup orchestration
- Repository layer (`AttachmentRepository`) is metadata-only DB access.

### API Surface (tickets-first rollout)

- `POST /api/tickets/{ticket_id}/attachments` (multipart upload)
- `GET /api/tickets/{ticket_id}/attachments` (entity attachment listing)
- `POST /api/attachments/{attachment_id}/signed-url` (short-lived signed URL generation)
- `GET /api/attachments/download/{token}` (secure download flow)
- `DELETE /api/attachments/{attachment_id}` (attachment + object deletion)
- `POST /api/attachments/cleanup-orphans` (admin orphan cleanup)

### Security Controls

- No database blobs; only metadata in DB.
- Server-side MIME sniffing from content signatures.
- Upload size limits via env-configurable max bytes.
- Role checks on upload/list/signed URL/delete/cleanup endpoints.
- Private object access flow through signed backend token endpoint.
- Audit hooks added for upload, download, delete, cleanup.

### Orphan Cleanup Strategy

- Compare storage keys in provider against metadata storage keys.
- Delete provider objects that are no longer referenced in metadata.
- Supports scoped cleanup by prefix.

### Current Scope and Expansion Path

- Tickets are the first linked entity in this rollout.
- Entity-type seam is present for future donor-device/invoice expansion.

## Gate 10: DevOps + CI/CD + Deployment Hardening + Observability

### Docker + Compose

- Backend Dockerfile added (Uvicorn app container).
- Frontend Dockerfile added (multi-stage build, Nginx static serve).
- Frontend Nginx config supports:
  - SPA fallback routing
  - `/api` reverse proxy to backend container
- Root `docker-compose.yml` added for local stack orchestration.

### Environment Configuration

- `.env.example` added with backend/security/storage/observability variables.
- Centralized runtime settings and validation in `app/core/settings.py`.
- Production/staging safeguards enforce non-default secrets.
- S3 provider validation enforces required credentials and bucket settings.

### CI/CD Pipeline Hardening

- Existing GitHub Actions workflow upgraded to staged flow:
  1. lint
  2. test
  3. build
  4. deploy
- Removed silent failure patterns (`|| true`) from quality gates.
- Build stage now validates Docker image builds for backend and frontend.
- Deploy stage gated to main-branch pushes with required secret checks.

### Observability

- Structured JSON logging configuration added.
- Request access log middleware added with request_id/user/method/path/status/duration.
- Centralized exception handlers added with:
  - standardized error envelope
  - stable `detail` field for backward compatibility
  - request_id correlation in responses
- Sentry-ready initialization hook added (env-driven, optional dependency).
- Async job queue now emits structured exception logs on failures.

### Operational Notes

- Keep `TECH_RESTORE_AUTH_BYPASS=0` for staging/production.
- Store all secrets in deployment provider secret stores.
- Prefer local provider only for dev; use S3-compatible provider for cloud.
- Use orphan cleanup endpoint in scheduled maintenance workflows.
