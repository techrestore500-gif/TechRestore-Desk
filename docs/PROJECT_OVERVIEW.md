# Project Overview

## Current stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI
- Database: SQLite
- Mode: local-first, offline-capable on one machine

## Current implemented scope

- backend app bootstrap and health check
- SQLite initialization on app startup
- seed data for supported device models and repair categories
- customers API
- repair tickets API
- ticket status history API
- ticket notes API
- supported device lookup API
- frontend dashboard shell
- intake wizard for customer and ticket creation
- tickets list page
- ticket detail page with note entry and status updates
- loaner inventory API and page
- loaner checkout and return API and page
- loaner overdue alerts on dashboard
- close-ticket guard when a loaner is still checked out
- pricing calculator API
- pricing warnings for approval-limit, replacement-value, and soldering exclusion
- repair action logging API and ticket-detail UI panel
- technician queue API (tickets grouped by status for daily workflow)
- technician hours logging API
- hours aggregation and reporting by technician
- hours attachment to tickets (optional, for detailed tracking)
- technician queue UI page
- technician hours log and summary UI page
- UI consistency pass for shell, dashboard, inventory, donors, queue, and hours pages
- queue page visual hierarchy improvements (status chips, grouped cards, elevated ticket interactions)
- hours page visual hierarchy improvements (panel styling, consistent controls, improved table contrast)
- tickets page responsive and interaction polish
- loaners page responsive and control-style polish
- settings page visual polish and constraint callouts
- intake page mobile comfort improvements (step progress metadata and stepper ergonomics)
- ticket-detail page section jump navigation and long-form readability polish
- parts inventory schema and API foundation
- donor devices schema and API foundation
- inventory UI page
- inventory usage inspector with recent ticket consumption history
- donor devices UI page
- donor page part-management UI with available/harvested part lists and selectors
- low-stock inventory endpoint
- ticket-detail parts-used logging (consumes inventory against repair actions)

## Intentionally not implemented yet

- reports and backups UI
- permissions and login
- multi-technician task assignment and collaboration

## Preserved business rules

- no standard soldering workflow in v1
- Cadence or S2720 charging-port repairs requiring soldering are not supported in normal flow
- microphone replacement requiring soldering is not supported in normal flow
- board-level repair is excluded from standard v1 workflow
- app remains local-first with no cloud dependency

## UI system documentation

- `docs/UI_SYSTEM_GUIDE.md` defines current layout, controls, color semantics, and interaction standards.