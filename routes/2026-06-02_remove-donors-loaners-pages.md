# 2026-06-02 - Remove Donors And Loaners Pages

## Goal

Remove Donors and Loaners as standalone frontend pages so they are no longer reachable from the app.

## Delivered

- Removed `/donors` and `/loaners` route entries from frontend router
- Removed Donors/Loaners items from sidebar navigation and Shop Tools nav group
- Removed Donors/Loaners quick links and related copy from Shop Tools page
- Removed command-palette search paths/results that navigated to `/donors` and `/loaners`
- Removed page-level label fallbacks for `/donors` and `/loaners` in app shell
- Deleted frontend Donors/Loaners page components and their tests

## Kept Intentionally

- Backend donor/loaner API endpoints and database tables remain intact
- Ticket-level loaner workflows and loaner agreement print flow remain intact

## Validation

- Frontend build: pass (`npm run build`)
- Backend tests: not required (frontend-only change)

## Notes

- This change removes standalone page access only; it does not delete customer/ticket/loaner/donor data
