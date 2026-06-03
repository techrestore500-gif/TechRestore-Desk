# 2026-06-03 Professional Redesign + Auth/Permissions Hardening

## What changed
- Redesigned shell to a formal professional layout with cleaner sidebar/top bar.
- Moved account actions into top-right avatar menu.
- Added in-shell password change modal and logout-on-success behavior.
- Added route-level role guard and explicit access denied page.
- Enforced owner-only Team Access route in frontend and backend.
- Enforced owner/admin-only pricing writes and settings route access.
- Added pricing read-only mode for technician/viewer in UI.
- Added explicit backend role dependencies across customers, tickets, pricing, reports, hours, repair-categories, and status-workflow routes.

## Files touched (high level)
- Frontend: app shell, router, role helpers, pricing permissions, role guard components, tests.
- Backend: auth/pricing/tickets/customers/repair-categories/status-workflow/hours/reports routes, API tests.
- Docs/report: implementation status update and professional redesign/auth report.

## Verification
- Backend API tests passed.
- Frontend tests passed.
- Frontend production build passed.

## Follow-up
- Optionally add dedicated E2E role matrix checks for direct URL guard behavior in browser automation.
- Optionally split front_desk-specific policy in a formal permissions matrix document if business wants stricter separation from admin.
