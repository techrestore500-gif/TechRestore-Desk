# Gate 4-6 Implementation Notes

## Scope

This milestone adds:

- Gate 4 operational audit logging
- Gate 5 internal typed event dispatch
- Gate 6 background job infrastructure (in-process + Arq worker scaffold)

## Audit Architecture

- Table: `activity_logs`
- Fields: `id`, `user_id`, `entity_type`, `entity_id`, `action`, `old_value`, `new_value`, `request_id`, `created_at`
- Write location: service layer only
- Sanitization:
  - payload depth limit
  - list/dict item caps
  - string truncation
  - sensitive key redaction (`password`, `token`, `secret`, etc.)

## Request Context + Middleware

- Added request context middleware that:
  - injects `X-Request-ID`
  - accepts caller-provided `X-Request-ID`
  - stores request context in contextvars
- Auth dependency now writes actor metadata into request context for service-side attribution.

## Event System

- In-process synchronous dispatcher with typed dataclass events.
- Initial event types:
  - `TicketCreatedEvent`
  - `TicketClosedEvent`
  - `InventoryLowEvent`
  - `DonorHarvestedEvent`
  - `LoanerOverdueEvent`
  - `PricingApprovedEvent`

## Background Jobs

- Added in-process queue with:
  - queue priorities: `critical`, `default`, `low`
  - retry support
  - idempotency keys
  - dead-letter persistence (`job_dead_letters`)
- Added `job_executions` table for idempotency completion tracking.
- Added Arq worker scaffold (`app/jobs/arq_worker.py`) for Redis-backed execution path.

## Initial Workflow Coverage

Audited actions now include:

- ticket creation/status changes/closure
- inventory part usage
- donor part harvesting
- loaner checkout/return
- pricing rules updates
- technician assignment changes
- admin user creation and role updates
- system template/default updates

## Migration Steps

1. Deploy code that includes new tables in `initialize_database()`.
2. Verify request headers include `X-Request-ID`.
3. Validate sensitive workflows create `activity_logs` entries.
4. Monitor dead-letter endpoint:
   - `GET /api/system/jobs/dead-letters`
5. Move queue execution to Arq workers when Redis infrastructure is ready.

## Operational Considerations

- Audit writes are synchronous and lightweight; payloads are trimmed to prevent oversized rows.
- Subscriber failures do not fail HTTP requests.
- Job dead letters provide immediate operator visibility.
- Arq integration is scaffolded and can be activated without changing service APIs.
