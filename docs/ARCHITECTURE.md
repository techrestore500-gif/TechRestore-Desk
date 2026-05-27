# Architecture

## Overview

Tech Restore Desk is a local-first, single-machine repair management application built for technicians to intake, diagnose, price, repair, and track phones in a Tech Restore repair facility. The app runs offline on a single Windows machine with no cloud dependency.

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite (development server with HMR)
- **Backend**: FastAPI (async Python web framework)
- **Database**: SQLite (local file-based, no setup required)
- **Networking**: HTTP via Vite dev server proxy and FastAPI

## Architecture Pattern

### Client-Server Model
```
Browser (React + TS)
    â†“ (HTTP proxy via Vite dev server /api â†’ http://127.0.0.1:8787)
Vite Dev Server (http://127.0.0.1:5173)
    â†“ (HTTP REST API calls)
FastAPI Backend (http://127.0.0.1:8787)
    â†“ (SQL)
SQLite Database (tech-restore-desk/data/tech_restore_desk.sqlite)
```

### Backend Structure

**`app/main.py`** â€” Application bootstrap and router registration
- Initializes database on startup
- Registers all route modules (health, customers, tickets, loaners, etc.)
- Serves as the main entry point for Uvicorn

**`app/database.py`** â€” Database schema, initialization, and data operations
- SQLite schema creation (tables for customers, tickets, loaners, etc.)
- SQL-based repository functions (list, get, create, update, patch, close)
- Business logic encapsulation (pricing, status transitions, repair action validation)
- Seed data insertion (supported models, repair categories)

**`app/models.py`** â€” Pydantic request/response contracts
- Input validation for all API endpoints
- Response serialization for consistent client contracts
- Type hints for all customer-facing data

**`app/routes/`** â€” API endpoint handlers
- `health.py` â€” health check endpoint
- `customers.py` â€” customer CRUD
- `tickets.py` â€” ticket lifecycle, notes, status, repair actions
- `loaners.py` â€” loaner checkout/return
- `dashboard.py` â€” summary metrics and alerts
- `pricing.py` â€” pricing calculation and rules
- `queue.py` (Phase 4) â€” technician queue by status
- `hours.py` (Phase 4) â€” time tracking and reporting

**`app/seed.py`** â€” Static seed data (supported devices, repair categories)

### Frontend Structure

**`src/components/`** â€” Reusable UI components
- `AppShell.tsx` â€” main navigation, page layout, phase banner

**`src/pages/`** â€” Page-level components (one per route)
- `DashboardPage.tsx` â€” overview, ticket summary, loaner alerts
- `IntakePage.tsx` â€” new customer and ticket intake form
- `TicketsPage.tsx` â€” searchable ticket list
- `TicketDetailPage.tsx` â€” ticket detail, status, notes, pricing, repair actions
- `LoanersPage.tsx` â€” loaner inventory, checkout, return
- `QueuePage.tsx` (Phase 4) â€” technician queue by status
- `HoursPage.tsx` (Phase 4) â€” time entry and hours reporting
- `SettingsPage.tsx` (future) â€” configuration

**`src/api/`** â€” API client and type definitions
- `tickets.ts` â€” fetch functions and TypeScript types for all API operations
- Uses standard `fetch()` API with JSON serialization

**`src/routes/`** â€” React Router configuration
- Defines URL mappings to pages

## Key Design Decisions

### Local-First Offline Architecture
**Decision**: No cloud, no authentication, no permissionsâ€”single-machine access only.

**Rationale**: 
- Tech Restore technicians work in one shop location with one device.
- Offline availability ensures work continues even if internet drops.
- Eliminates infrastructure overhead and compliance burden.
- Data stays on-premises under customer control.

**Implication**: Scaling to multi-location or multi-user requires significant redesign (auth, sync, cloud DB). Current design is not suitable for multi-tenant SaaS.

### Database-Centric Business Logic
**Decision**: Core business logic lives in `app/database.py` alongside SQL operations, not in separate service classes.

**Rationale**:
- Single-machine app with no complex concurrency issues.
- Keeps database schema knowledge and logic in one place.
- Reduces file fragmentation and import verbosity.
- Fast iteration on new features.

**Implication**: As complexity grows (Phase 5+), consider extracting to separate service/domain classes. For now, this is pragmatic.

### Pydantic for Input Validation and Serialization
**Decision**: All API input is validated via Pydantic models; responses use Pydantic to serialize.

**Rationale**:
- Catches invalid input early (bad phone numbers, negative prices, invalid statuses).
- Automatic JSON serialization and deserialization.
- IDE type hints throughout the codebase.
- Self-documenting API contracts.

### React State via Fetch + Re-render
**Decision**: No state management library (Redux, Zustand, etc.). Pages fetch data on load and re-fetch on user action.

**Rationale**:
- Small app with few cross-page dependencies.
- Simpler mental model: each page is responsible for its own data.
- Easier to debug (no complex state mutations).

**Implication**: High-frequency re-fetches (e.g., real-time queue updates) would be inefficient. For Phase 4+ queue polling, consider adding WebSocket or polling logic.

### Seed Data vs. User-Created Entities
**Decision**: Supported models and repair categories are seeded once on startup; customers and tickets are user-created.

**Rationale**:
- Supported devices and repair workflows are static business policy.
- Customers and tickets grow over time with real work.
- Keeps schema bootstrap predictable.

**Implication**: Adding a new supported device requires code change + database restart. Consider admin UI for future phases.

## Database Schema Philosophy

- **Immutable history**: Status changes, notes, and repair actions are append-only (create-only, never delete).
- **Soft deletes**: Customers and tickets are never hard-deleted; logic uses status or flags.
- **Denormalization for UX**: Some fields are denormalized (e.g., `ticket.estimated_replacement_value`) to avoid complex joins.
- **Audit trail**: Most tables have `created_at` and `updated_at` for traceability.

## API Contract Stability

All API responses are JSON. Common patterns:

**Success (2xx)**:
```json
{
  "id": 1,
  "field": "value",
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00"
}
```

**List (2xx)**:
```json
[
  { "id": 1, "field": "value" },
  { "id": 2, "field": "value" }
]
```

**Error (4xx/5xx)**:
```json
{
  "detail": "Human-readable error message"
}
```

## Security Model

**Current (Phase 0-4)**:
- No authentication, no authorization, no encryption.
- App assumes single technician in a locked-down shop environment.
- SQLite file permissions rely on OS-level file access control.

**Future (Phase 7 Polish)**:
- Consider role-based access (admin, technician, front-desk).
- Optional password lock on app startup.
- Encrypted SQLite database file.

## Performance Assumptions

- **Single technician**: No concurrent database writes (no optimistic locking needed).
- **Small dataset**: ~1000s of tickets per year, not millions.
- **Single machine**: No network latency considerations.
- **Vite dev server**: Sufficient for single-user development; production would use `npm run build` + static serve.

**Implication**: Current architecture will degrade at 10,000+ tickets or with multi-user writes. Revisit caching and indexing if needed.

## Error Handling Strategy

**Backend**:
- Validation errors (400 Bad Request): Pydantic catches invalid input.
- Logic errors (400 Bad Request): Business rule violations (e.g., soldering exclusion, close-with-active-loaner).
- Not found (404): Ticket/customer ID doesn't exist.
- Server errors (500): Unexpected exceptions logged to console.

**Frontend**:
- Catches fetch errors and displays toast/alert to user.
- Logs errors to browser console for debugging.
- No error tracking service (could add Sentry in Phase 7).

## Testing Strategy (Current)

- **Manual smoke tests**: API calls via PowerShell; UI navigation in browser.
- **No automated test suite yet**: Phase 4+ should add pytest for backend, Vitest for frontend.

See [TEST_PLAN.md](TEST_PLAN.md) in the spec folder for planned testing phases.

## Deployment and Runtime

**Development**:
```powershell
# Backend (from tech-restore-desk/backend)
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787

# Frontend (from tech-restore-desk/frontend)
npm run dev
```

**Production** (Phase 7):
- Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8787` (with HTTPS reverse proxy).
- Frontend: `npm run build` â†’ static files served by reverse proxy or Tauri.
- Database: Scheduled backups via script.

## Known Limitations and Technical Debt

1. **No automated testing**: Manual validation only. Add pytest + Vitest in Phase 4.
2. **Hardcoded pricing defaults**: Constants in `database.py`; no admin UI to edit.
3. **No search optimization**: Linear scan for ticket search (OK for <10k tickets).
4. **No pagination**: All lists returned in full; OK for <1000 items per list.
5. **TypeScript moduleResolution**: Recently changed from `Node` to `Bundler` to fix TS6 deprecation.
6. **No rate limiting**: Could add if multi-user in future.
7. **Seed data not versioned**: If schema changes, seed data may need manual migration.

## Next Architecture Decisions (Phase 4+)

- **Technician Queue**: Consider real-time updates (WebSocket) vs. polling refresh button.
- **Hours Reporting**: Add date range filtering; consider caching aggregations.
- **Inventory**: Add transaction/movement log to track part usage over time.
- **Reports**: Add in-memory caching of aggregations; trigger recalculation on data change.



