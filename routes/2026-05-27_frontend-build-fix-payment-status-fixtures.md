# 2026-05-27 Frontend Build Fix: Ticket payment_status Test Fixtures

## Summary
Resolved frontend production build failures caused by strict ticket typing after `payment_status` became required on ticket summary/detail payloads.

## Changes
- Updated frontend test ticket fixtures to include `payment_status` with realistic default values (`"unpaid"`) in:
  - `src/pages/InvoicePrintPage.test.tsx`
  - `src/pages/TicketDetailPage.test.tsx`
  - `src/pages/TicketsPage.test.tsx`
  - `src/pages/IntakePrintPage.test.tsx`
  - `src/pages/DashboardPage.test.tsx`
  - `src/hooks/queries/useTicketsQuery.test.tsx`
- Kept `TicketDetail` type strict (no optional downgrade) and aligned fixtures with current API contract.
- Fixed Dashboard ticket refresh flow to match current `useAsyncData` API by reloading via a dependency counter in `src/pages/DashboardPage.tsx`.

## Validation
- `npm run build` passes (`tsc --noEmit && vite build`).
- `vitest run src/pages/InvoicePrintPage.test.tsx src/pages/TicketDetailPage.test.tsx src/pages/TicketsPage.test.tsx` passes.

## Operational note
- Frontend static bundle is now ready for Render redeploy retry from a TypeScript/build perspective.
