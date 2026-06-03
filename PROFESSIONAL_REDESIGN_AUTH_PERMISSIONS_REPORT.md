# PROFESSIONAL_REDESIGN_AUTH_PERMISSIONS_REPORT

## Scope Delivered
This pass implemented a professional UI shell redesign and tightened frontend/backend access controls for owner/admin/technician/viewer behavior. It also added route-level role enforcement, pricing read-only behavior for non-admin roles, owner-only invite/user-role management, and expanded automated tests.

## Frontend Redesign
- Reworked the main shell to a formal, restrained workspace style with a cleaner sidebar and neutral top bar.
- Moved account controls into a top-right avatar menu.
- Added account menu actions:
  - Account / Profile
  - Change password
  - Logout
- Added in-shell change-password modal flow and forced re-auth on successful password update.
- Reduced playful visual treatment and aligned base global styles to a professional enterprise tone.

## Frontend Access Control Changes
- Added route-level role guard component (`RequireRole`) to block direct URL bypass.
- Added access denied surface (`AccessDeniedPage`) for forbidden route access.
- Enforced owner-only access to team invites route (`/users-invites`).
- Enforced owner/admin access for settings route (`/settings`).
- Enforced explicit role access on pricing route with read-only behavior for non-owner/admin.
- Added shared role helper module for consistent role checks.

## Pricing Permissions (Frontend)
- Owner/admin: full pricing edit/create/update/delete operations.
- Technician/viewer: pricing read access only.
- Read-only banner and disabled controls shown when user cannot edit.

## Backend Permission Hardening
Updated role dependencies across API routes:

- `auth` routes:
  - Owner-only: users list/create, user role patch, invite list/create/revoke/resend.
- `pricing` routes:
  - Owner/admin only for write endpoints (`PATCH`/`POST`/`DELETE` on defaults and catalog).
  - Read endpoints remain available to authenticated roles.
- `tickets` routes:
  - Technician explicitly allowed to create tickets.
  - Explicit read-role protections added to list/get/history/notes/repair-actions endpoints.
- `customers` routes:
  - Read allowed to owner/admin/front_desk/technician/viewer.
  - Write restricted to owner/admin/front_desk/technician.
- `repair-categories` routes:
  - Read allowed to authenticated roles.
  - Write restricted to owner/admin.
- `status-workflow` routes:
  - Read allowed to authenticated roles.
  - Patch restricted to owner/admin.
- `hours` routes:
  - Read endpoints allow owner/admin/front_desk/technician/viewer.
  - Write endpoints restricted to owner/admin/front_desk/technician.
- `reports` summary:
  - Explicit authenticated role dependency added.

## Automated Test Coverage Added/Updated
### Backend
- Added auth-enforced fixture and helper login flow.
- Added tests for:
  - owner-only invite enforcement (admin forbidden)
  - invite reuse rejection after accept
  - pricing write restrictions by role
  - technician ticket create allowed / viewer forbidden
  - password change and re-auth behavior

### Frontend
- Added `RequireRole` tests.
- Added `PricingPage` permission test for read-only mode.
- Added `AppShell` role-navigation tests verifying owner-only Team Access visibility and settings/team visibility rules by role.
- Updated existing tests for current Settings and command palette behavior.

## Validation Results
- Backend tests: `39 passed`.
- Frontend tests: `55 passed`.
- Frontend production build: successful (`tsc --noEmit && vite build`).

## Manual Verification Checklist
- [ ] Owner can open Team Access and manage invites.
- [ ] Admin cannot open Team Access (forbidden view).
- [ ] Direct URL to `/users-invites` as non-owner shows Access Denied.
- [ ] Technician/viewer can open Pricing but cannot edit controls.
- [ ] Owner/admin can create/update/delete pricing catalog entries.
- [ ] Account menu appears in top-right with profile/change-password/logout actions.
- [ ] Password change forces logout and requires fresh login.
- [ ] Viewer cannot create tickets.
- [ ] Technician can create tickets.
- [ ] Settings route is blocked for non-owner/admin.

## Notes
- The route hardening keeps owner implicit admin-superuser semantics where backend `require_role("admin")` already allows owner.
- Some existing role names (for example `front_desk`) are preserved for compatibility with current data model and workflows.
