# Implementation Notes and Decision Log

This document captures decisions, patterns, and lessons learned during development. It helps new developers understand *why* the code is structured the way it is, and what pitfalls to avoid.

## 2026-05-25 Quick Intake Redesign

### Bottlenecks Identified

- Intake required six wizard steps and many non-critical fields, slowing walk-in ticket creation.
- Status updates required form-style edits instead of tap/click actions.
- Ticket list interaction was table-heavy with small action targets and high scan friction.
- Detail page mixed high-frequency workflow actions with advanced pricing configuration, increasing cognitive load.

### Workflow Direction Chosen

- Replaced stepper intake with a single-screen Quick Intake form focused on nine primary fields.
- Added customer name typeahead using existing `/api/customers` search and direct autofill for known customers.
- Added recent-device suggestions from recent ticket history for faster brand/model entry.
- Moved primary operational workflow to a Service Desk dashboard card board with visible status chips.
- Implemented one-click status targets with backend-safe transition pathing (multi-hop updates when needed).
- Simplified repair detail into workflow-first sections: customer info, payment snapshot, timeline/history, append-only notes log, parts used.

### Lesson

For repair shops, speed and clarity beat completeness. Keep advanced fields and configuration available, but keep the default intake and tracking path optimized for the first 15 seconds of customer interaction.

## 2026-05-26 Twilio Voicemail Integration

### Decisions Made

- Added Twilio settings persistence in SQLite so the app can store account SID, phone number, and an obfuscated auth token without exposing the token back to the frontend.
- Added a voice webhook that returns TwiML for unanswered calls and records voicemail audio locally through Twilio callbacks.
- Added a voicemail inbox page so recordings can be reviewed, listened to, marked, archived, and linked into repair intake.

### Lesson

Keep voice integrations local-first and backend-owned. The browser should only render inbox state and playback controls; it should never need direct access to Twilio secrets.

## 2026-05-26 Twilio V1 Scope Simplification

### Decisions Made

- Simplified TwiML to a basic voicemail loop using greeting + recording callback only for improved reliability in early rollout.
- Kept voicemail inbox focused on practical desk actions: play recording, mark listened, mark done, add notes, and copy caller number.
- Added a setup status panel in Settings that shows credential/base URL readiness, exact webhook URLs to paste into Twilio, recording callback route status, and the last received voicemail timestamp.
- Final operator wording in the inbox uses simple status names: New, Listened, and Done.

### Lesson

For a repair shop rollout, a stable voicemail loop is more valuable than early CRM automation. Keep the first version predictable and observable before adding conversion workflows.

## 2026-05-26 Global Layout and Spacing Consolidation

### Decisions Made

- Standardized page-level form and action spacing around shared theme primitives instead of per-page ad hoc flex/grid snippets.
- Added global overflow guardrails (`box-sizing`, control `min-width` and `max-width` constraints) so split-screen and narrow laptop layouts do not clip or push horizontal scroll.
- Migrated high-traffic operational screens (Settings, Intake, Inventory, Donors, Loaners, Tickets, Dashboard, Ticket Detail, Voicemail) to shared layout tokens and reduced bespoke inline spacing blocks.

### Lesson

In an inline-style-heavy React codebase, a small set of explicit layout primitives prevents repeated regressions and makes responsive fixes predictable across the whole app.

## 2026-05-26 Twilio Playback Bugfix

### Decisions Made

- Fixed voicemail playback failures caused by Twilio recording fetches returning TLS certificate verification errors in local Windows runtime.
- Updated the voicemail audio proxy route to map Twilio fetch failures to actionable API responses instead of generic internal errors.
- Added a retry path that falls back to a non-verified TLS fetch only when certificate verification fails, to preserve local operator playback reliability.
- Expanded recording callback parsing to persist `Caller` and `Called` when `From` and `To` are not present.

### Lesson

When browser audio controls show 0:00/0:00 for server-backed media, confirm the media endpoint status and content-type first. JSON error payloads to an audio source often look like silent playback failures.

## 2026-05-27 Twilio Voice Quality Refinement

### Decisions Made

- Switched TwiML greeting speech to a natural Twilio-supported Polly voice (`Polly.Joanna`) instead of the previous default robotic voice.
- Broke greeting delivery into shorter sentence chunks with pauses to improve trust and clarity for callers.
- Added optional `voicemail_greeting_audio_url` settings support so TwiML can use `<Play>` for future uploaded or recorded greetings without refactoring the webhook flow.

### Lesson

For small-shop phone UX, pacing matters as much as wording. Short, deliberate speech chunks sound more human and reduce caller confusion.

## Architecture Decisions

### Backend: Monolithic `database.py` Over Layered Architecture

**Decision**: All database schema, migrations, and business logic live in `app/database.py` rather than separated into repositories, services, and domain layers.

**Rationale**:
- Single-machine, single-technician app with no multi-threaded/concurrent writes.
- Keeps database schema knowledge in one place (easier to understand).
- Reduces import boilerplate and file fragmentation.
- Fast iteration: no need to propagate changes through multiple layers.

**Trade-off**:
- As feature count grows (Phase 5+), the file will become large (~2000 LOC).
- More experienced developers might prefer separation of concerns.

**Mitigation** (Phase 5):
- Consider extracting services: `pricing_service.py`, `loaner_service.py`, etc.
- Implement repository pattern if adding database abstraction layer (e.g., for testing).

**Lesson**: Don't over-engineer for scale you don't have yet. Monolithic structures are fine for small apps.

---

### Frontend: No State Management Library

**Decision**: React pages manage state locally with `useState()` and fetch data on mount. No Redux, Zustand, or Context API for global state.

**Rationale**:
- App is small with few cross-page dependencies.
- Each page (Dashboard, Tickets, Loaners) is relatively self-contained.
- Simpler mental model: no hidden state mutations.
- Easier to debug: state changes are visible in component code.

**Trade-off**:
- Re-fetching data when navigating is inefficient (e.g., Dashboard â†’ Tickets â†’ Dashboard re-fetches from scratch).
- No shared state across pages (have to pass data via URL params or re-fetch).

**Mitigation** (Phase 4+):
- If queue updates are needed in real-time (technician refreshing every 30 seconds), add polling logic in `QueuePage.tsx`.
- If cross-page data sharing becomes essential, introduce Context API (lighter than Redux).

**Lesson**: State management libraries are over-hyped for small apps. Use them only when complexity forces your hand.

---

### Database: SQLite Over PostgreSQL or Other

**Decision**: SQLite for local-first, file-based storage. No server setup required.

**Rationale**:
- Tech Restore runs on a single Windows machine with no network infrastructure.
- SQLite is zero-config, zero-administration.
- Full-text search via SQL extension possible if needed later.
- Backups are just file copies.

**Trade-off**:
- No multi-process writes (concurrency is handled via OS file locking, which is basic).
- Schema migrations are manual (no Alembic or Flyway integration yet).
- Scaling to multiple machines requires rearchitecting (migration to PostgreSQL + sync logic).

**Mitigation** (Phase 7):
- If moving to multi-location, plan PostgreSQL migration with schema versioning.
- Add backup automation to prevent data loss.

**Lesson**: Choose the simplest tool that solves the problem. For single-machine, SQLite is a no-brainer.

---

## Code Organization Patterns

### API Response Consistency

**Pattern**: All API responses follow a consistent shape.

**Success (200/201)**:
```json
{
  "id": 1,
  "field": "value",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**List (200)**:
```json
[
  { "id": 1, ... },
  { "id": 2, ... }
]
```

**Error (4xx/5xx)**:
```json
{
  "detail": "Human-readable message"
}
```

**Benefit**: Frontend can reliably parse responses without conditional logic.

**How to Maintain**: Every new endpoint should return Pydantic models with `id`, `created_at`, `updated_at`. Validate in code review.

---

### Parameterized Queries to Prevent SQL Injection

**Pattern**: All SQL queries use `?` placeholders, never f-strings or string concatenation.

**Example (Good)**:
```python
cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
```

**Example (Bad)**:
```python
cursor.execute(f'SELECT * FROM tickets WHERE id = {ticket_id}')  # SQL INJECTION RISK
```

**Benefit**: Prevents malicious SQL injection if untrusted data is passed.

**How to Maintain**: Code review should flag any SQL strings with `f"..."` or `+`.

---

### Immutable Status History

**Pattern**: Status changes are appended to `status_history` table; the `status` field on the ticket is denormalized but updated in tandem.

**Benefit**:
- Audit trail: can see when and why ticket status changed.
- No data loss: cannot accidentally delete historical records.
- Supports reporting: "How many tickets were in diagnosis for >2 days?"

**Implementation** (in `database.py`):
```python
def update_ticket_status(conn, ticket_id: int, new_status: str, changed_by: str, note: str):
    # Update current status
    cursor.execute('UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?', 
                   (new_status, datetime.now(), ticket_id))
    # Append history
    cursor.execute('INSERT INTO status_history (ticket_id, status, changed_by, changed_at, note) VALUES (?, ?, ?, ?, ?)',
                   (ticket_id, new_status, changed_by, datetime.now(), note))
    conn.commit()
```

**How to Maintain**: Never update status without appending history. Code review should flag missing history inserts.

---

### Soft Deletes (No Hard Deletes)

**Pattern**: Customers and tickets are never deleted. Statuses or flags mark records as inactive.

**Benefit**:
- No accidental data loss.
- Audit trail remains intact.
- Can "undelete" if needed.

**Implementation**:
- Use status values like "Inactive" or add a `is_deleted` boolean.
- Filter in queries: `WHERE is_deleted = false` or `WHERE status != 'Inactive'`.

**How to Maintain**: Code review should flag any `DELETE FROM` statements (unless deleting test data).

---

## Testing Patterns

### Manual Smoke Tests Over Automated Tests (Phase 0-3)

**Current Approach**: PowerShell scripts that create customer â†’ ticket â†’ loaner â†’ status changes, verify responses.

**Example**:
```powershell
$customer = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/api/customers ...
$ticket = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/api/tickets ...
$response = Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8787/api/tickets/$($ticket.id)/status ...
Write-Output "Success: $($response.status)"
```

**Benefit**: Quick feedback during development. Easy to follow manually.

**Trade-off**: Not reproducible, not part of CI/CD, easy to forget to run.

**Mitigation** (Phase 4+): Introduce pytest for backend, Vitest for frontend. Start with critical paths (intake, pricing, loaner).

---

## Common Mistakes and How to Avoid Them

### Mistake 1: Forgetting to Restart Backend After Adding Routes

**Problem**: New route is added to `app/routes/tickets.py`, but API returns 404.

**Cause**: FastAPI only discovers routes on startup. `--reload` watches file changes but doesn't always re-import new route files properly.

**Solution**: Kill backend (Ctrl+C) and restart `uvicorn app.main:app --reload --host 127.0.0.1 --port 8787`.

**Prevention**: After adding routes, manually test with curl/PowerShell before assuming it works.

---

### Mistake 2: Modifying TypeScript Types Without Backend Response

**Problem**: Frontend calls `/api/tickets/5`, which returns JSON. Frontend tries to access `ticket.repair_actions`, but type says it's optional.

**Cause**: Backend response was updated, but frontend type definition wasn't.

**Solution**: Ensure `TicketDetail` type in `src/api/tickets.ts` matches backend `TicketDetailResponse` in `app/models.py`.

**Prevention**: After modifying backend response, update frontend type. Use IDE to validate: hover over API response assignment, check inferred type.

---

### Mistake 3: Hardcoding API Base URL

**Problem**: Frontend code contains `http://127.0.0.1:8787` in multiple places. Hard to change for production.

**Cause**: Hardcoded strings are quick, but not scalable.

**Solution**: Define base URL once in `src/api/tickets.ts`:
```typescript
const API_BASE = '/api';  // Vite proxy handles /api â†’ http://127.0.0.1:8787
```

**Prevention**: Code review should flag any hardcoded URLs.

---

### Mistake 4: Forgetting Loaner Return in Close Guard

**Problem**: Technician tries to close ticket, but API rejects it with "active loaner" error. Technician forgets to return loaner first.

**Cause**: UI doesn't clearly surface loaner status on ticket detail.

**Solution**: Add prominent alert on `TicketDetailPage`: "âš ï¸ Loaner checked out. Return it before closing ticket."

**Prevention**: UI/UX review should catch missing guards.

---

### Mistake 5: Soldering Repair Action Accepted When It Shouldn't Be

**Problem**: Technician adds a "Microphone Repair" action via API, but it should be rejected.

**Cause**: Forgot to check `requires_soldering` flag in repair category.

**Solution**: In `add_repair_action()`, verify category doesn't have `requires_soldering = true`. Raise `ValueError` if it does.

**Prevention**: Add test case: "Attempt to add soldering-required action â†’ expect 400 error."

---

## TypeScript Configuration Gotchas

### moduleResolution: Node â†’ Bundler

**Issue**: TS 5.0+ deprecated `moduleResolution: "Node"`. TS 6.0+ will error.

**Solution**: Change `tsconfig.json`:
```json
{
  "compilerOptions": {
    "moduleResolution": "Bundler"
  }
}
```

**Lesson**: Keep dependencies up to date; check deprecation warnings in logs.

---

## Database Schema Evolution

### Adding a Column

1. Add column definition to `CREATE TABLE` in `initialize_database()`.
2. Delete `tech-restore-desk/data/tech_restore_desk.sqlite` to trigger re-init.
3. Restart backend.
4. All data is lost (OK for dev; not for production).

**Future** (Phase 7): Implement Alembic migrations or similar.

---

### Adding a Table

1. Add `CREATE TABLE` statement in `initialize_database()`.
2. Add seed data if needed.
3. Implement `get_*()`, `list_*()`, `create_*()` functions in `database.py`.
4. Add Pydantic models in `models.py`.
5. Create routes in `routes/*.py`.
6. Test via API.

---

## Performance Observations

### SQLite Performance is Fine for <10k Tickets

**Observation**: Queries are instant even with full-table scans. No indexing needed yet.

**When to Index** (Phase 5+):
- Full-text search on ticket notes â†’ add FTS (Full-Text Search) extension.
- Reports with date range filters â†’ add index on `created_at`.
- Search by customer â†’ add index on `customer_id`.

**How to Profile**: Use `.timer on` in sqlite3 CLI to see query times.

---

### Vite HMR Sometimes Stale

**Observation**: Frontend changes don't always hot-reload. Hard refresh (Ctrl+Shift+R) needed.

**Workaround**: Kill `npm run dev` and restart if HMR isn't working.

**Lesson**: Hot Module Replacement is convenient but not bulletproof. Always have a hard refresh ready.

---

## Documentation Maintenance

### Why Docs Need to Stay in Sync

**Issue**: Code changes but docs don't â†’ new developers are confused.

**Solution**:
- Update docs *alongside* code changes.
- API_REFERENCE.md documents all endpoints â†’ keep in sync with routes.
- ARCHITECTURE.md documents patterns â†’ update if patterns change.
- BUSINESS_RULES.md documents constraints â†’ update if rules change.

**Frequency**: Update docs with every feature commit. Treat docs as "living documentation," not archived artifacts.

---

## Lessons for Next Phases (Phase 4+)

### Before Phase 4: Add Test Suite

- Write pytest tests for backend endpoints (intake, pricing, loaner, close guard).
- Write Vitest tests for React components (TicketDetailPage, QueuePage, HoursPage).
- Aim for 80%+ coverage of critical paths.

### Before Phase 5: Document Inventory Schema

- Plan parts table and part usage tracking.
- Document how part usage affects pricing (cost of goods sold).
- Define donor device lifecycle (add, harvest, retire).

### Before Phase 6: Plan Reporting Infrastructure

- Decide on aggregation strategy (in-app vs. exported CSVs vs. real-time dashboards).
- Design report filters (date range, technician, device model, repair category).
- Plan caching to avoid slow queries on large datasets.

### Before Phase 7: Security Hardening

- Add authentication (optional password).
- Add role-based access (admin, technician, front-desk).
- Encrypt database file.
- Implement session timeouts.
- Add rate limiting if multi-user.

---

## Code Review Checklist

When reviewing PRs/changes:

- [ ] API responses have `id`, `created_at`, `updated_at`.
- [ ] SQL queries use parameterized `?` placeholders.
- [ ] Status changes append to history.
- [ ] No hard deletes (use soft deletes or status flags).
- [ ] Frontend types match backend Pydantic models.
- [ ] No hardcoded API URLs (use `/api` proxy).
- [ ] Business rules are enforced (soldering, approval, loaner guard).
- [ ] Error messages are user-friendly.
- [ ] Docs are updated (API_REFERENCE, BUSINESS_RULES, ARCHITECTURE if applicable).

---

## Questions and Open Issues

1. **Should we add OpenAPI/Swagger docs?** Yes, FastAPI auto-generates `/docs` endpoint. Expose it for developer reference (Phase 7).
2. **Should we version the API?** Not yet. v0 pre-release. Plan versioning if breaking changes become frequent (Phase 6+).
3. **Should we add logging beyond print()?** Yes, add `logging` module in Phase 4. Log all API requests, errors, and state changes.
4. **Should we support multi-technician hours tracking?** Yes, Phase 4 should track `technician` name per time entry. Aggregate by technician on reports.
5. **What about data backup?** Phase 7 will add automated daily backup script. For now, manual copies of `tech_restore_desk.sqlite`.



