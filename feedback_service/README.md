# Feedback Portal Service

This service is intended for deployment at `feedback.techrestoredesk.com`.

## Environment variables

- `FEEDBACK_PORTAL_PASSWORD` (required): shared 14-character password.
- `FEEDBACK_PORTAL_SESSION_SECRET` (required): random signing secret.
- `FEEDBACK_PORTAL_DB_PATH` (optional): defaults to `feedback_portal.sqlite`.
- `FEEDBACK_PORTAL_INGEST_TOKEN` (optional): token required by `/ingest` endpoint.

## Local run

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\feedback_service"
pip install -r requirements.txt
python run.py
```

Then open `http://localhost:8890`.
