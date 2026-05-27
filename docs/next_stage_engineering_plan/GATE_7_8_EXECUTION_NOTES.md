# Gate 7 + Gate 8 Execution Notes

## Gate 7 Frontend Scalability

### Architecture

- TanStack Query introduced for server-state query/mutation orchestration.
- Zustand introduced for UI-only state:
  - filters
  - command palette state
  - scanner mode toggles
  - pagination controls
- Query provider and error boundary wired at app root.

### Query Patterns

- Query keys centralized in `frontend/src/hooks/queryKeys.ts`.
- Reusable hooks added under `frontend/src/hooks/queries/`.
- Optimistic inventory mutations added under `frontend/src/hooks/mutations/`.

### Reusable Table System

- New generic table component:
  - sorting
  - pagination
  - row actions
  - bulk actions

### UX Modernization

- Command palette foundation implemented.
- Keyboard shortcut foundation implemented (`Ctrl/Cmd + K`, `Escape`).
- Scanner-friendly input primitive added for fast operational search/filter flows.

### Migration Scope (This Pass)

- Tickets page migrated to query + reusable table.
- Queue page migrated to query with optimistic assignment updates and quick filter.
- Inventory page migrated to query hooks and optimistic stock mutations.

### Technical Debt Remaining

- Not all pages are migrated yet; some still use custom `useAsyncData`.
- Server-side pagination is now consumed for inventory movement ledger, but most legacy endpoints remain list-all.
- Command palette result ranking is intentionally simple and should move to weighted relevance later.

## Gate 8 Inventory Intelligence Foundation

### Ledger + Reconciliation Schema

- Added inventory movement ledger table.
- Added reconciliation records table.
- Movement types supported:
  - `add`
  - `consume`
  - `adjust`
  - `transfer`
  - `donor_harvest`
  - `return`
  - `correction`

### Service Ownership

- Inventory service now owns movement creation for stock mutations.
- Movement creation wired for:
  - part creation with initial stock
  - manual stock adjustments
  - repair-action consumption
  - donor harvest stock increment
  - reconciliation correction when applied

### Reconciliation Workflows

- Reconciliation endpoint records expected vs actual.
- Optional `apply_adjustment` generates correction movement and updates stock.

### API Additions

- Movement listing endpoint with pagination/filters.
- Manual stock adjustment endpoint.
- Reconciliation create/list endpoints.

### Alerting Hook

- Low-stock event publishing is now called after stock-impacting service operations.

### Operational Considerations

- Ledger writes are synchronous for consistency and forensic usefulness.
- Movement payload includes request and actor context where available.
- Supports future analytics read models without requiring BI stack now.
