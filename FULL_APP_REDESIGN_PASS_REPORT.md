# Full App Redesign Pass — Report

**Date:** 2026-05-31  
**Rollback SHA (pre-redesign baseline):** `07e9d8d4cf1bb9768bac5bfc7453daeef2800ce7`  
**Build status:** ✅ Clean (`tsc --noEmit && vite build` — 0 errors, 0 warnings)

---

## Goal

Make Tech Restore Desk feel like a clean, fast, pleasant repair-desk app instead of a broad admin console. Audit source: `FULL_APP_PRODUCT_UI_UX_AUDIT.md`.

---

## Files Changed

| File | Change Type |
|---|---|
| `frontend/src/components/AppShell.tsx` | Restructured nav, profile card, spacing |
| `frontend/src/components/PageChrome.tsx` | New — shared PageHeader component (was missing) |
| `frontend/src/styles/theme.ts` | Compact token pass + new utility tokens |
| `frontend/src/pages/VoicemailPage.tsx` | Filter chips, compact grid row layout |
| `frontend/src/pages/DashboardPage.tsx` | Tighter metric cards, board grid |
| `frontend/src/pages/QueuePage.tsx` | Density improvements, theme token adoption |
| `frontend/src/pages/IntakePage.tsx` | Tighter form sections and status chips |
| `frontend/src/pages/SettingsPage.tsx` | Section label visual improvement |
| `frontend/src/pages/TicketDetailPage.tsx` | Tighter detail grid and timeline rows |
| `frontend/src/pages/HoursPage.tsx` | Tighter form and session action gaps |

---

## What Changed

### AppShell — Navigation Restructure

The single flat nav list was replaced with three named groups:

- **Core**: Dashboard, New Repair, Tickets, Queue, Hours, Voicemail, Inventory
- **Operations**: Loaners, Donors
- **Admin**: Reports, Team Access (admin/owner only), Settings

Account/Profile was moved out of the nav entirely and into a **profile card** at the bottom of the sidebar. The card shows name, email, role, an "Account" link, and a "Sign out" button.

Additional sidebar changes:
- Brand tagline changed from "Local-first repair workflow" → "Repair workflow" (shorter, fits better)
- Sidebar width unchanged at 210px
- Brand padding reduced: `16px 16px 12px`
- Nav padding reduced: `10px 8px`
- NavLink padding reduced: `9px 14px` → `7px 10px`, font from `0.92rem` → `0.88rem`, radius `12px` → `10px`
- Nav group label style: `0.62rem` uppercase, muted color `#7a9490`

### theme.ts — Global Compact Token Pass

Every shared token was made slightly tighter to reduce visual noise across all pages simultaneously:

| Token | Before | After |
|---|---|---|
| `panel` padding | `20px` | `16px 18px` |
| `primaryBtn` padding | `12px 18px` | `9px 18px` |
| `secondaryBtn` padding | `12px 18px` | `9px 18px` |
| `miniBtn` padding | `8px 12px` | `6px 11px`, added `fontSize: 0.83rem` |
| `input` padding | `12px 14px` | `9px 12px` |
| `subCard` padding | `14px 16px` | `10px 14px` |
| `statusBadge` padding | `10px 14px` | `7px 14px` |
| `formStack` gap | `14px` | `12px` |
| `formActionsRow` gap | `10px` | `8px` |
| `pageWrap` gap | `18px` | `16px` |

New tokens added:
- `successBanner` — green success feedback banner
- `notice` — muted grey informational notice
- `sectionDivider` — thin hr-style divider helper

### VoicemailPage — Compact Inbox Layout

The voicemail list was redesigned from a flex layout into a **CSS grid** with fixed columns (`90px 1fr 1fr 1fr 80px 140px`), making the inbox feel like a proper compact inbox rather than a card list.

Quick filter chips row was added at the top (All / New / Listened / Done) with live counts per status. Clicking a chip filters the list immediately.

The Play button and ⋮ menu remain in the last grid column as an inline action row.

### DashboardPage — Compact Metric Cards

- Metric cards: padding `14px 16px` → `12px 14px`, value font `2rem` → `1.75rem`, label `0.78rem` → `0.72rem`
- Board grid gap: `12px` → `10px`
- Ticket card padding: `14px` → `12px 14px`
- New Repair button: padding `12px 18px` → `9px 18px`

### QueuePage — Density and Token Adoption

- Section card padding: `1rem` → `12px 14px`
- Section header font: `1.06rem` → `0.97rem` with explicit `fontWeight: 700`
- Ticket card gap: `1rem` → `8px`, padding `1rem` → `10px 12px`
- Empty state: "No tickets in this status." → "No tickets here." (smaller, muted color)
- All buttons (`Refresh`, `Save view`, view chips) now use shared `t.primaryBtn`, `t.secondaryBtn`, `t.miniBtn`
- View name input uses `t.input`
- Delete chip "x" → "×" (proper typographic symbol)

### IntakePage — Tighter Form Layout

- Panel border radius: `24px` → `20px`
- Form section gap: `12px` → `10px`
- Section title font: `0.77rem` → `0.73rem`
- Two-column grid gap: `16px 18px` → `12px 16px`
- Status chip padding: `10px 12px` → `7px 12px`, font `0.84rem` → `0.82rem`

### SettingsPage — Section Label Visual Hierarchy

Section labels gained a subtle bottom border and adjusted spacing to visually separate setting groups:

- Font: `0.78rem` → `0.72rem`
- Added `paddingBottom: 6px`, `borderBottom: "2px solid rgba(27,79,69,0.12)"`, `marginTop: 4px`

### TicketDetailPage — Tighter Detail Grid

- `detailGridStyle` gap: `12px` → `10px`
- Invoice link padding: `8px 12px` → `7px 12px`
- Timeline row padding: `10px 12px` → `8px 12px`

### HoursPage — Tighter Form Gaps

- Clock session action area: `marginTop 18px` → `14px`, button row gap `10px` → `8px`
- Filter form gap: `16px` → `12px`
- Manual hours form gap: `16px` → `12px`

### PageChrome.tsx — New Shared Component

`PageHeader` component was missing from the codebase but imported by DonorsPage, InventoryPage, and LoanersPage, causing build failures. The component was created:

- Accepts `kicker` (uppercase eyebrow text), `title`, and `description` (ReactNode)
- Renders a consistent page header matching the app's visual language

---

## What Did NOT Change

- `frontend/src/routes/router.tsx` — All routes intact. No routes removed or modified.
- All backend code, APIs, database schema — unchanged.
- Auth system — JWT, roles, AuthGateMiddleware — unchanged.
- Twilio webhooks — still publicly accessible at `/api/twilio/voice` and `/api/twilio/recording`.
- Loaner and Donor pages — code intact, routes intact, just moved to Operations nav group.
- All existing functionality — no features were removed.

---

## Build Results

```
vite v5.4.21 building for production...
✓ 145 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.31 kB
dist/assets/index-Ci718ETi.css    0.23 kB │ gzip:   0.16 kB
dist/assets/index-CxFEwCgc.js   442.71 kB │ gzip: 128.06 kB
✓ built in 2.96s
```

---

## Rollback Instructions

If a rollback is needed before deploying:

```bash
# Soft rollback — revert all redesign commits
git revert HEAD

# Hard rollback — go back to exact pre-redesign state
git reset --hard 07e9d8d4cf1bb9768bac5bfc7453daeef2800ce7
```

---

## Deploy Order

1. Push `main` to origin
2. Render frontend static site rebuilds automatically on push
3. No backend changes — no backend redeploy needed
4. No database migrations needed
