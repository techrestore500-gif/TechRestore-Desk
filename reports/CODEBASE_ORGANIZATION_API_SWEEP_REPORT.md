# Codebase Organization & API Sweep Report

**Date:** June 1, 2026  
**Scope:** Full frontend/backend sweep — organization, route correctness, imports, naming, legacy cleanup  
**Result:** All issues resolved. Build passes. 53 frontend tests pass. 126 backend tests pass.

---

## 1. Summary of What Was Found

The primary blocker was a **307 Temporary Redirect** on the Hours page when fetching the hours list. The root cause was a missing trailing slash in the frontend API call. Beyond that, a large amount of inventory and hours code was misplaced inside `api/tickets.ts`, making the codebase hard to reason about and error-prone.

**Root causes discovered:**
- `fetchHours` called `GET /api/hours` — backend requires `GET /api/hours/` (FastAPI redirects with 307 without trailing slash)
- `logHours` called `POST /api/hours` — backend requires `POST /api/hours/`
- All hours types and functions lived in `api/tickets.ts` — zero connection to tickets
- All inventory/parts/donor types and functions also lived in `api/tickets.ts`
- Three pages and four hooks also imported inventory symbols from `api/tickets`
- No dedicated `api/hours.ts` or `api/inventory.ts` existed

---

## 2. Known Hours Bug — Root Cause and Fix

**Root cause:** FastAPI registers the list-hours route as `@router.get("/")` under the `/hours` prefix, making the effective path `/api/hours/` (with trailing slash). When the frontend called `/api/hours` without a trailing slash, FastAPI issued a `307 Temporary Redirect` to `/api/hours/`. The browser followed the redirect but lost the Authorization header on the redirected GET, causing the auth gate to reject the request, which surfaced as `Failed to fetch` or a 401 on the Hours page.

**Fix:**
- `fetchHours` now calls `GET /api/hours/` (trailing slash)
- `logHours` now calls `POST /api/hours/` (trailing slash)
- `fetchHoursSummary`, `fetchActiveClockSession`, `clockIn`, `clockOut` were already calling sub-paths (`/summary`, `/active`, `/clock-in`, `/clock-out`) and did not need trailing slash changes

---

## 3. API Modules Inspected

| File | What It Contained Before Sweep |
|---|---|
| `api/client.ts` | HTTP client, auth wiring — clean, no changes needed |
| `api/auth.ts` | Auth types, login, logout, user management — clean, no changes needed |
| `api/tickets.ts` | Tickets + customers + loaners + dashboard + pricing + repair categories + queue + **hours** + **inventory** — oversized |
| `api/system.ts` | System backup, export, voicemail, Twilio settings — clean but re-exported voicemails via tickets.ts |
| `api/health.ts` | Health check — clean |
| `api/hours.ts` | **Did not exist** — created in this sweep |
| `api/inventory.ts` | **Did not exist** — created in this sweep |

---

## 4. API Modules Changed / Split

### Created: `frontend/src/api/hours.ts`

Contains all technician time-tracking API code, previously embedded in `tickets.ts`:

- **Types:** `HoursLog`, `HoursClockSession`, `HoursClockOutResult`, `HoursSummary`
- **Functions:** `fetchHours`, `fetchHoursSummary`, `fetchActiveClockSession`, `clockIn`, `clockOut`, `logHours`
- **Fixed:** Trailing slash added to `fetchHours` (`/api/hours/`) and `logHours` (`/api/hours/`)

### Created: `frontend/src/api/inventory.ts`

Contains all inventory, parts, donor device, and purchase API code, previously embedded in `tickets.ts`:

- **Types:** `Part`, `DonorDevice`, `PartUsage`, `InventoryMovement`, `InventoryMovementPage`, `InventoryReconciliation`, `InventoryPurchaseItem`, `InventoryPurchase`, `InventoryPurchaseList`
- **Functions:** `fetchParts`, `createPart`, `updatePart`, `deletePart`, `fetchLowStockParts`, `fetchPartUsage`, `fetchRepairActionPartUsage`, `logPartUsage`, `adjustPartStock`, `fetchDonors`, `createDonor`, `updateDonor`, `harvestPartFromDonor`, `fetchInventoryMovements`, `reconcilePartStock`, `fetchInventoryReconciliations`, `fetchInventoryPurchases`

### Modified: `frontend/src/api/tickets.ts`

Removed all hours types/functions and inventory types/functions. The file now contains only ticket-domain code:
- Ticket types and CRUD
- Customer types and CRUD
- Loaner types and CRUD
- Dashboard summary/alerts
- Pricing, repair categories, status workflow
- Queue (technician queue)
- Reports summary

---

## 5. Frontend Imports Changed

| File | Change |
|---|---|
| `pages/HoursPage.tsx` | Import from `../api/hours` instead of `../api/tickets` |
| `pages/HoursPage.test.tsx` | Import + vi.mock from `../api/hours` instead of `../api/tickets` |
| `pages/InventoryPage.tsx` | Import from `../api/inventory` instead of `../api/tickets` |
| `pages/DonorsPage.tsx` | Import from `../api/inventory` instead of `../api/tickets` |
| `pages/DonorsPage.test.tsx` | Import + vi.mock from `../api/inventory` instead of `../api/tickets` |
| `pages/OperationsPage.tsx` | Split: inventory symbols from `../api/inventory`, loaner from `../api/tickets` |
| `pages/TicketDetailPage.tsx` | `fetchRepairActionPartUsage` and `PartUsage` from `../api/inventory` |
| `pages/TicketDetailPage.test.tsx` | `fetchRepairActionPartUsage` mock from `../api/inventory` |
| `hooks/mutations/useInventoryMutations.ts` | Import from `../../api/inventory` |
| `hooks/queries/useInventoryQueries.ts` | Import from `../../api/inventory` |
| `hooks/queries/useGlobalSearchQuery.ts` | `fetchDonors`/`fetchParts` from `../../api/inventory`; `fetchTickets`/`fetchLoaners` stay in `../../api/tickets` |

---

## 6. Route / Path Mismatches Found and Fixed

| Endpoint | Before | After | Reason |
|---|---|---|---|
| Hours list | `GET /api/hours` | `GET /api/hours/` | Backend route `@router.get("/")` under `/hours` prefix requires trailing slash |
| Log manual hours | `POST /api/hours` | `POST /api/hours/` | Same reason |
| Hours summary | `GET /api/hours/summary` | No change — sub-path, no trailing slash needed |
| Active session | `GET /api/hours/active` | No change |
| Clock in | `POST /api/hours/clock-in` | No change |
| Clock out | `POST /api/hours/clock-out` | No change |

**No other 307-prone endpoints were found.** All other routes with explicit sub-paths (`/api/tickets/{id}`, `/api/customers`, etc.) are not affected because they are defined as named paths, not as `"/"` under a prefix.

**Note on convention:** The trailing-slash issue is a FastAPI default behavior (`redirect_slashes=True`). The hours router is the only place where the root collection endpoint is `"/"` under a prefixed router registered at the app level via `include_router(..., prefix="/api")`. Future routes should be defined with explicit paths (e.g., `@router.get("/hours")` at the app level, or `@router.get("/")` only when the prefix is registered without a conflicting redirect path).

---

## 7. Legacy Names / Storage Keys Found and Fixed

**`localStorage` keys in `HoursPage.tsx`:** The page already had correct handling:
- Reads from `techRestore.techRoster` (current key)
- Falls back to `tag.techRoster` (legacy key) and migrates the value to the new key on first read
- No changes needed — the migration logic is already correct

**No other `tag.*`, `FlipFix`, or old-branding keys were found** in any frontend files.

---

## 8. Error Handling Improvements

No new error handling changes were made in this sweep. Existing error handling in hours functions was carried over cleanly to `api/hours.ts` and follows the same pattern as the rest of the codebase:
- `clockIn` failure → shows "Failed to clock in" (already specific)
- `clockOut` failure → shows "Failed to clock out" (already specific)
- `logHours` failure → shows backend `detail` message or HTTP status code

No generic `[object Object]` or raw technical errors were found in the hours flow.

---

## 9. Backend Changes

**No backend changes were made.** All issues were on the frontend. The backend routes, schemas, and services are correct. The trailing-slash behavior is a documented FastAPI default and does not need to change; the frontend was simply not matching the declared route.

---

## 10. Tests / Build Run

| Suite | Result |
|---|---|
| Frontend TypeScript build (`tsc --noEmit + vite build`) | ✅ Passed — 0 errors, 149 modules |
| Frontend tests (`vitest --run`) | ✅ 53 tests passed across 24 test files |
| Backend tests (`pytest app/tests/ -q`) | ✅ 126 tests passed |

---

## 11. Files Changed

**Created:**
- `frontend/src/api/hours.ts`
- `frontend/src/api/inventory.ts`
- `reports/CODEBASE_ORGANIZATION_API_SWEEP_REPORT.md`

**Modified:**
- `frontend/src/api/tickets.ts` — removed hours and inventory sections
- `frontend/src/pages/HoursPage.tsx`
- `frontend/src/pages/HoursPage.test.tsx`
- `frontend/src/pages/InventoryPage.tsx`
- `frontend/src/pages/DonorsPage.tsx`
- `frontend/src/pages/DonorsPage.test.tsx`
- `frontend/src/pages/OperationsPage.tsx`
- `frontend/src/pages/TicketDetailPage.tsx`
- `frontend/src/pages/TicketDetailPage.test.tsx`
- `frontend/src/hooks/mutations/useInventoryMutations.ts`
- `frontend/src/hooks/queries/useInventoryQueries.ts`
- `frontend/src/hooks/queries/useGlobalSearchQuery.ts`

**Backend: no files changed.**

---

## 12. Deploy Order

1. **Frontend redeploy required** — source files changed.
2. **Backend redeploy NOT required** — no backend changes.

Deploy order: frontend only.

---

## 13. Manual Verification Checklist

Work through each item after deploying the new frontend build:

- [ ] **Hours page loads** — no `Failed to fetch` banner on page open
- [ ] **Hours history request returns 200** — check Network tab; `GET /api/hours/?technician=...` should return 200, not 307
- [ ] **Clock in works** — click Clock In, session appears as active
- [ ] **Clock out works** — click Clock Out, session closes and hours entry appears in the list
- [ ] **Manual hours entry works** — fill in date/hours/description, submit, entry appears in list
- [ ] **Summary totals display** — hours summary by technician is shown on the page
- [ ] **Active session shows** — when clocked in, the active session timer/badge is visible
- [ ] **Ticket pages still load** — open Tickets list and a Ticket Detail, no errors
- [ ] **Voicemail page loads** — voicemails display correctly
- [ ] **Login / auth still works** — sign out, sign back in, token is preserved
- [ ] **Inventory page loads** — parts and purchase records display
- [ ] **Donors page loads** — donor devices and available parts display
- [ ] **Operations page loads** — loaner and donor/inventory metrics display
- [ ] **Global search returns tickets, parts, donors** — type in the command palette
- [ ] **Queue page loads** — technician queue displays

---

## 14. Remaining Cleanup Suggestions

These were intentionally not changed in this sweep to keep scope focused. They are low-priority but worth doing in a future cleanup pass.

### `api/tickets.ts` is still large

Even after removing hours and inventory, `tickets.ts` contains customer functions (`fetchCustomers`, `fetchCustomer`, `fetchCustomerTickets`), loaner functions (a dozen), dashboard functions, pricing, repair categories, status workflow, queue, and reports. A future split could be:
- `api/customers.ts` — customer types and CRUD
- `api/loaners.ts` — loaner types and CRUD
- `api/queue.ts` — technician queue
- `api/reports.ts` — reports summary

These would require updating ~10 more import sites. No bugs are caused by leaving them in place.

### Backend route prefix style is inconsistent

Most routers carry their own prefix (e.g., `APIRouter(prefix="/api/tickets")`), but `hours_router` and `queue_router` are registered with `app.include_router(..., prefix="/api")` at the app level. This is functionally equivalent but inconsistent. Consider adding the `/api` prefix directly to those routers in a future cleanup.

### `tickets.ts` re-exports voicemails from `system.ts`

Line 2 of `tickets.ts`:
```ts
export { fetchVoicemails, updateVoicemail, type VoicemailRecord } from "./system";
```
This is a convenience re-export but could confuse maintainers. Any page that imports voicemail from tickets.ts should import from `system.ts` or a future `api/voicemail.ts` directly. No pages currently do this (they import from `system.ts`), so the re-export is harmless but unnecessary.

### Error messages

The `client.ts` `getJson` function produces `Request failed: 401` on session expiry. This is developer-facing (the auth gate intercepts 401 and redirects to login), so it rarely surfaces to users. If it does appear, a friendlier message like "Your session expired. Please sign in again." would be better. The `auth.ts` module already has a `friendlyAuthError` helper that could be reused in `getJson`.
