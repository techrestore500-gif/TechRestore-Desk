# Implementation Status

## Completed

### Architecture Gates (Latest)
- 2026-06-02 Hours frontend feature removed: removed the Hours page route, nav entries, quick links, keyboard shortcut target, and Hours-only frontend API/page/test files; backend hours endpoints and tables were intentionally left in place for low-risk compatibility
- 2026-06-02 Hours selected-day hardening follow-up complete: frontend now normalizes incoming `work_date` values before selected-day filtering, per-day aggregation, and latest-day selection, and renders date-only values using local calendar parsing to prevent timezone-shifted day history
- 2026-06-02 Hours data correctness pass complete: monthly calendar now renders per-day logged totals inside day cells, selected-day totals are computed from actual selected-day entries (not month summary), month-range totals are shown explicitly, and hours queries are technician-filter-aware
- 2026-06-02 Backend hours date filtering hardened: `work_date` values are normalized to `YYYY-MM-DD` on write and all list/summary filters compare with `DATE(work_date)` so legacy datetime-like values still appear under correct day selections
- 2026-06-02 Hours history visibility fix complete: Hours page now uses local-date defaults (not UTC date slices) and auto-jumps to the most recent logged work date when the initially selected day has no entries, preventing false "missing hours" screens
- 2026-06-02 Hours display formatting updated to clock notation (`H:MM`): time values now render like `2:15` instead of decimal-hour notation like `2.25` across active session elapsed time, selected-day totals, and day history entries
- 2026-06-02 Hours logging switched to minute-based UX: manual logging now accepts whole minutes instead of decimal-hour points, and hours surfaces now render elapsed session time, day totals, and history rows in hour/minute format
- 2026-06-02 Queue frontend removed and app palette reshaped again: deleted the dedicated Queue page/hook/test and removed queue-specific UI wiring from nav, shortcuts, store, and page links, while retheming the shared shell/auth/page-chrome layers to a warmer neutral terracotta/olive palette
- 2026-06-02 Real data reset/import tooling complete: added a SQLite-only protected backend script that backs up the active database, wipes ticket/hour trees, preserves auth/settings/Twilio data, and imports the real Tech Restore repair, pricing-note, inventory-note, and Mattis hours records
- 2026-06-02 Global color palette refresh complete: updated app-wide palette tokens to a new blue/coral scheme and propagated it through global background layers, shared theme tokens, app shell navigation surfaces, auth gate, and shared page chrome components
- 2026-05-31 Dashboard/Ticket status-transition UI fix complete: status actions now render from workflow-valid reachable transitions only (with primary actions + overflow menu), preventing frontend-offered actions that backend rejects; dashboard recent-customer phone display now uses shared phone formatter
- 2026-05-31 UX redo phase 2 complete: page-level IA reshaped on Dashboard, Operations, Tickets, and Settings into workflow-lane command surfaces; full frontend build and tests remain green
- 2026-05-31 Full frontend UX redo foundation complete: replaced global visual language, shared token system, AppShell, shared page chrome, and shared DataTable presentation for a distinct new product feel while preserving existing route/workflow behavior and test coverage
- 2026-05-28 SMTP invite delivery hardening complete: added SMTP mode toggles (`SMTP_USE_SSL`, `SMTP_STARTTLS`) and timeout control (`SMTP_TIMEOUT_SECONDS`), added safe SMTP diagnostics that log mode/host/port without credentials, and added protected bootstrap invite resend endpoint (`POST /api/auth/bootstrap/resend` with `X-Bootstrap-Key`) to recover first-admin onboarding without database reset
- 2026-05-28 Invite-only authentication rollout complete: removed public signup/access-request endpoints and UI, switched login to email+password only, added admin invite management (create/revoke/resend/list), added public invite resolve/accept flow at `/invite/:token`, and replaced bootstrap link retrieval with SMTP-emailed one-time bootstrap owner/admin invites driven by environment configuration
- 2026-05-28 Account-based authentication rollout complete: replaced temporary shared-password frontend gate with username/email + password login, added pending signup request flow, introduced admin/owner access-request approval with role assignment, and added startup bootstrap owner creation from environment variables when user table is empty
- 2026-05-28 Frontend auth gate production fix complete: app now enforces shared-password login when `VITE_AUTH_ENABLED=true`, injects bearer token from centralized API client, and cleanly resets to login on `401` responses (including expired token handling)
- 2026-05-27 Frontend production build stability fix complete: updated ticket summary/detail test fixtures to include required `payment_status`, aligned additional related fixtures surfaced by strict typing, and restored dashboard ticket list reload behavior for current async hook API
- 2026-05-27 Production hosting prep complete: frontend API base URL is environment-driven, backend supports `PORT`/`FRONTEND_ORIGIN`/`DATABASE_URL`, Twilio env credentials are server-side only, and Twilio public webhook routes are separated from private Twilio settings/inbox routes
- 2026-05-27 Settings page control-center overhaul complete: new quick-jump navigation, live settings status tiles, clearer section grouping for Business/Communications/Workflow/System, and roadmap visibility while preserving all existing API-backed settings workflows and validation behavior
- 2026-05-27 Twilio voice quality refinement complete: voicemail greeting now uses a natural Polly voice with paced conversational chunks, and TwiML is now compatible with future Play-based custom greeting audio URLs
- 2026-05-26 Twilio playback bugfix complete: voicemail audio proxy now handles Twilio fetch failures safely, maps playback errors to actionable API responses, and includes SSL-certificate fallback for local Windows environments
- Gate 9 complete: attachment metadata schema, storage-provider abstraction (local + S3-compatible), secure upload/download/delete flows, signed URL flow, and orphan cleanup endpoint
- Gate 10 complete: Dockerfiles + docker-compose, environment validation, CI/CD staged workflow hardening, structured logging, centralized error handling, and Sentry-ready hooks
- Prompt 11 complete: query instrumentation, slow-query metrics endpoints, pagination for tickets/audit logs, queue query consolidation, and index optimization pass
- Prompt 12 complete: persisted operational UI state, queue/ticket saved views, faster quick actions, and expanded keyboard shortcuts
- Prompt 13 complete (evaluation only): SaaS-readiness assessment with blocker analysis and migration roadmap
- Gate execution notes added in `docs/next_stage_engineering_plan/GATE_9_10_EXECUTION_NOTES.md`
- Next-stage reports added:
	- `docs/next_stage_engineering_plan/PROMPT_11_PERFORMANCE_QUERY_OPTIMIZATION_REPORT.md`
	- `docs/next_stage_engineering_plan/PROMPT_12_OPERATIONAL_UX_REFINEMENT_REPORT.md`
	- `docs/next_stage_engineering_plan/PROMPT_13_SAAS_READINESS_EVALUATION.md`

### Phase 0
- backend scaffold
- frontend scaffold
- SQLite initialization
- health endpoint
- supported model and repair category seed data
- basic navigation shell

### Phase 1
- customer create, list, read, update API
- ticket create, list, read, update API
- ticket status history API
- ticket notes API
- supported model lookup API
- intake wizard UI (superseded by Quick Intake single-screen workflow)
- tickets list UI
- ticket detail UI

### Phase 2
- loaner phone inventory API and UI
- loaner checkout and return API and UI
- deposit tracking fields in checkout and return
- dashboard loaner alerts API and dashboard rendering
- ticket close guard for active loaners

### Phase 3
- pricing calculator API and ticket-detail pricing panel
- approval warning logic in pricing calculation
- replacement-value warning in pricing calculation
- soldering-exclusion warnings in pricing flow
- repair action logging API and ticket-detail action list

### Phase 4
- technician queue API (tickets grouped by status for daily workflow)
- technician hours logging API
- technician live clock-session API (`/api/hours/active`, `/api/hours/clock-in`, `/api/hours/clock-out`)
- hours aggregation and reporting by technician and date
- technician queue UI page
- technician hours log, summary, and live clock UI page
- technician queue UI visual refresh (priority section cards, status chips, elevated ticket cards)
- technician hours UI visual refresh (consistent panels, controls, improved hours table readability, and Mattis-first daily workflow defaults)

## Completed Follow-through

### Phase 5 (Completed)
- parts inventory schema and API foundation (parts, part usage, donor devices)
- inventory routes (`/api/inventory/parts`, `/api/inventory/donors`, `/api/inventory/low-stock`)
- inventory UI page
- inventory usage inspector (last-used timestamp, total consumed, recent ticket usage)
- donor devices UI page
- donor part management with named part chips (available vs harvested)
- donor part selection via dropdowns (no raw ID entry required)
- donor part-harvest workflow endpoint
- low-stock query endpoint
- ticket-detail "parts used" logging UI (repair action + part + quantity)
- repair-action part usage query endpoint (`/api/inventory/repair-actions/{id}/parts`)
- validation smoke tests completed for create/list/harvest flows
- inventory purchase ledger endpoints and UI integration (`/api/inventory/purchases`)

### Phase 5 docs
- `docs/DECISIONS.md` created from spec answers
- `docs/PHASE_5_SPEC.md` created with schema, API, UI, and test scope

### Phase 6 (Completed)
- reports API and UI expanded: date-range summary now supports technician and repair-category filters plus technician/category breakdowns
- local backup and export workflow implemented: Settings page can create local SQLite backups, download JSON snapshots, and review recent backup/export activity
- print-friendly forms implemented: invoice, intake form, and loaner agreement print views are all available from ticket detail

### Phase 7 (Substantially Completed)
- UI polish and responsive design delivered across shell, dashboard, inventory, donors, queue, hours, tickets, loaners, and settings
- settings and operations configurability delivered for pricing, categories, status workflow, agreements, and templates
- shared UI token system and async data/reload patterns standardized
- expanded frontend tests and responsive interaction improvements completed

## Remaining roadmap (Post-MVP / optional)

### Phase 8 candidates (next)
- role-based permissions (technician, manager, admin)
- authentication and session management
- transactional intake endpoint to atomically create customer + ticket
- optional cloud sync and scheduled backup automation
- multi-technician collaboration and assignment workflow

### UI documentation
- `docs/UI_SYSTEM_GUIDE.md` added as the visual and interaction consistency reference

## Implementation Complete

All **MVP-scope features** have been fully implemented and tested. The application meets all 13 MVP acceptance criteria and includes all "Must-have for v1" features from the specification.

### MVP Features Delivered:
- Full ticket and customer lifecycle management
- Loaner device checkout/return workflow with defaults
- Technician hours logging and clock-in/out
- Pricing calculation with persisted configurable defaults
- Status workflow transitions with configurable rules and guardrails
- Repair category management
- Notification template customization
- Local backup and export
- Queue grouping by status
- Inventory management with parts and donors
- Reports and analytics
- Print-friendly forms (intake, invoice, loaner agreement)
- Full responsive UI with shared design tokens

## Future Enhancements (Optional)

The following items are intentionally deferred as optional enhancements per the project specification:
- role-based permissions (technician, manager, admin) — listed as "Could-have later" in Feature List; explicitly excluded from MVP scope
- authentication and session management — depends on permissions; not required for local single-user app
- Tauri packaging for standalone executable — listed as "Optional packaging later"; web app is production-ready as-is


## Current known limitations

- intake creates customer and ticket sequentially rather than via a single transactional endpoint
- loaner selection is still intentionally excluded from intake wizard and managed on the Loaners page
- multi-technician collaboration and task assignment not yet supported
- no automated scheduled backup or cloud sync currently implemented (manual backup, JSON export, and recent local activity history are available from Settings)