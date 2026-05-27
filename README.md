# Tech Restore Desk App

Phase 0 scaffold for the local-first Tech Restore Desk app.

This phase includes:
- FastAPI backend skeleton
- SQLite database initialization
- supported device and repair category seed data
- health endpoint
- React + TypeScript + Vite frontend shell

Current implemented slice:
- customer creation API
- repair ticket create/list/detail API
- ticket status history API
- ticket note API
- supported model lookup API
- intake wizard UI
- ticket list UI
- ticket detail UI
- loaner inventory API
- loaner checkout and return API
- loaner overdue and alert summary API
- ticket close endpoint with active-loaner guard
- loaner management UI
- pricing calculation API
- pricing warning logic (approval limit, replacement value, soldering exclusion)
- repair action logging API
- pricing and repair action panel in ticket detail UI
- technician queue API (tickets grouped by status for daily workflow)
- technician hours logging API
- hours aggregation and reporting by technician and date
- technician queue UI page
- technician hours log and summary UI page
- UI consistency pass across shell/dashboard/inventory/donors/queue/hours pages
- queue page visual refresh with grouped status cards and clearer ticket hierarchy
- hours page visual refresh with cohesive form/filter panels and improved log table readability
- tickets page responsive and interaction polish
- loaners page responsive and control-style polish
- settings page visual polish and constraint callouts
- parts inventory schema and API foundation
- donor devices schema and API foundation
- inventory UI page
- inventory usage inspector with recent consumption history
- donor devices UI page
- donor part-management UI with named available/harvested part lists
- ticket-detail parts-used logging workflow tied to repair actions

Phase 5 in progress. Advanced reports, multi-technician collaboration, role permissions, and packaging/deployment are still not implemented.

## Project structure

```text
tech-restore-desk/
  backend/
    app/
      main.py
      database.py
      models.py
      seed.py
      routes/
        health.py
    requirements.txt
  frontend/
    src/
      api/
      components/
      pages/
      routes/
  data/
  backups/
  docs/
```

## Backend setup

From `tech-restore-desk/backend`:

```powershell
C:/Users/owner/AppData/Local/Programs/Python/Python314/python.exe -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

Health endpoint:

```text
http://127.0.0.1:8787/api/health
```

## Frontend setup

From `tech-restore-desk/frontend`:

```powershell
npm install
npm run dev
```

Frontend dev URL:

```text
http://127.0.0.1:5173
```

The Vite dev server proxies `/api` requests to the local FastAPI backend.

For production builds, set `VITE_API_BASE_URL` (for example `https://api.example.com`).

## Docker quick start

From `tech-restore-desk/`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Services:

- frontend: `http://127.0.0.1:5173`
- backend API: `http://127.0.0.1:8787`

## Attachment storage

- Attachments use object storage abstraction and metadata rows in SQLite.
- No file blobs are stored in the database.
- Default development provider is local filesystem storage under `data/attachments`.
- S3-compatible provider can be enabled through environment variables in `.env`.

## Notes

- SQLite database file is created under `tech-restore-desk/data/tech_restore_desk.sqlite`.
- SQLite database files in `data/` are local dev data and are ignored by `.gitignore`.
- Seed data is limited to supported device models and repair categories for Phase 0.
- Soldering-required repair categories remain flagged as unsupported for standard v1 workflow.
- App-level implementation notes live in `tech-restore-desk/docs/`.
- Visual consistency guidelines live in `tech-restore-desk/docs/UI_SYSTEM_GUIDE.md`.
- Production hosting runbook lives in `tech-restore-desk/docs/PRODUCTION_DEPLOYMENT.md`.

