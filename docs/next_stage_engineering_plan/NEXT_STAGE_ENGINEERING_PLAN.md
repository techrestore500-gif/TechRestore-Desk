# TECH RESTORE DESK - NEXT STAGE ENGINEERING PLAN
## GATED IMPLEMENTATION ROADMAP

ROLE:
You are acting as a senior staff engineer, systems architect, and SaaS infrastructure consultant helping evolve an operational repair-shop platform called "Tech Restore Desk".

This is NOT a toy CRUD app.
This is NOT a coding tutorial.
This is NOT a generic SaaS starter.

You are helping evolve a real workflow-heavy operational platform.

## PROJECT CONTEXT
### STACK

Frontend:
- React
- TypeScript
- Vite

Backend:
- FastAPI
- SQLite (current)
- SQLAlchemy migration planned

Development:
- VS Code
- GitHub Copilot

Architecture Style:
- Modular monolith

### EXISTING SYSTEM FEATURES

The platform already includes:
- Repair ticket lifecycle
- Customer management
- Technician queues
- Inventory tracking
- Donor-device harvesting
- Loaner-device lifecycle
- Pricing logic
- Operational dashboards
- Technician hours tracking
- Workflow validation systems
- Queue management
- Inventory consumption history

This is already operational business software.

## CORE ENGINEERING GOALS

Primary goals:
- Improve maintainability
- Introduce architecture discipline
- Prevent technical debt explosion
- Prepare for multi-user scaling
- Prepare for PostgreSQL migration
- Add authentication + RBAC
- Add audit/event systems
- Improve frontend scalability
- Maintain operational UX speed
- Prepare long-term SaaS evolution

## NON-NEGOTIABLE ENGINEERING RULES

DO
- Improve incrementally
- Preserve existing workflows
- Keep architecture understandable
- Prioritize maintainability
- Prioritize operational reliability
- Use modular monolith patterns
- Prefer explicit code over magic abstractions
- Keep files reasonably small
- Design for future scale without overengineering

DO NOT
- Introduce microservices
- Rewrite the app unnecessarily
- Add fake enterprise complexity
- Generate generic boilerplate architecture
- Add abstractions without purpose
- Break working workflows
- Prioritize animations over operational UX
- Add premature distributed systems

## Gate 1: Backend Architecture Discipline

Objective: Refactor the backend into clean architectural boundaries.

Target structure:
- backend/app/routes/
- backend/app/services/
- backend/app/repositories/
- backend/app/schemas/
- backend/app/models/
- backend/app/core/
- backend/app/auth/
- backend/app/events/
- backend/app/jobs/
- backend/app/middleware/
- backend/app/utils/

Requirements:
- Routes: HTTP only, request parsing, response formatting, auth checks.
- Services: workflow logic, validation coordination, business rules, orchestration.
- Repositories: database access only.
- Schemas: Pydantic request/response typing.
- Models: SQLAlchemy ORM, PostgreSQL-ready.

Deliverables:
- Folder structure
- Migration plan
- Example service pattern
- Repository examples
- Refactor examples

Reasoning:
- Prevent logic leakage into routes.
- Makes testing faster and changes safer.
- Enables easier auth/audit insertion later.

Tradeoffs:
- Short-term refactor cost.
- Temporary duplicate schema/model definitions during transition.

Migration strategy:
1. Start with one high-impact workflow (close ticket).
2. Extract service + repository.
3. Add service-focused tests.
4. Repeat workflow by workflow.

Scalability impact:
- Clear seams for adding workers, auth, and events.
- Reduces coupling as team size grows.

Example pattern:
```python
# route
@router.post("/tickets/{ticket_id}/close")
def close_ticket(ticket_id: int, payload: CloseTicketRequest, user=Depends(require_role("front_desk"))):
    result = ticket_service.close_ticket(ticket_id=ticket_id, actor_id=user.id, payload=payload)
    return CloseTicketResponse.model_validate(result)

# service
def close_ticket(self, ticket_id: int, actor_id: int, payload: CloseTicketRequest):
    ticket = self.ticket_repo.get_for_update(ticket_id)
    self.rules.ensure_can_close(ticket)
    updated = self.ticket_repo.close(ticket_id, payload.final_price, payload.note)
    self.audit.log(...)
    self.events.publish(TicketClosed(...))
    return updated
```

Best practices:
- One service method per business action.
- Keep repositories dumb and predictable.
- Service tests mock repositories and validate rules.

Pitfalls:
- Fat repositories with business rules.
- Route-level transaction management.
- utils becoming dumping ground.

## Gate 2: Database Evolution

Objective: Prepare the database for production-grade multi-user usage.

Requirements:
- Migrate toward SQLAlchemy ORM, Alembic, PostgreSQL compatibility.
- Add created_at, updated_at, optional deleted_at to major tables.
- Add enums for statuses.
- Add inventory movement ledger.
- Add future-ready nullable location_id and tenant_id columns.

Deliverables:
- Schema improvements
- Migration strategy
- Indexing recommendations
- FK recommendations
- Normalization recommendations

Reasoning:
- Better integrity and migration safety.
- Ledger unlocks traceability and analytics.

Tradeoffs:
- More migrations and stricter schema discipline.
- Enum migrations need care.

Migration strategy:
1. Introduce SQLAlchemy models without deleting current logic.
2. Backfill timestamps.
3. Add enums with compatibility mapping.
4. Add ledger and dual-write from inventory operations.
5. Remove old paths once stable.

Indexing and FK recommendations:
- tickets(status, updated_at)
- tickets(customer_id), tickets(technician_id), tickets(location_id)
- inventory_movements(part_id, created_at)
- inventory_movements(ticket_id), inventory_movements(actor_user_id)
- Unique constraints on business identifiers
- FK ON DELETE RESTRICT for critical records

Example ledger model:
```python
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = mapped_column(BigInteger, primary_key=True)
    part_id = mapped_column(ForeignKey("parts.id"), index=True, nullable=False)
    movement_type = mapped_column(Enum(MovementType), nullable=False)
    quantity = mapped_column(Integer, nullable=False)
    reason = mapped_column(String(120), nullable=True)
    ticket_id = mapped_column(ForeignKey("tickets.id"), nullable=True)
    actor_user_id = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

Pitfalls:
- Writing ledger for only some inventory actions.
- Missing idempotency for adjustments/imports.
- Hard-deleting business records too early.

## Gate 3: Authentication + RBAC

Objective: Introduce professional user management.

Required roles:
- admin
- technician
- front_desk

Requirements:
- Protected API routes
- JWT/session auth
- Permission middleware
- Role-aware frontend rendering

Reasoning:
- Needed for accountability and controlled operations.

Tradeoffs:
- Session/login UX overhead.
- More role-based test permutations.

Migration strategy:
1. Optional auth in dev mode.
2. Protect sensitive writes first.
3. Expand to read-route protection.
4. Enforce mandatory auth once covered.

Scalability impact:
- Enables controlled multi-user growth and audit trust.

Example policy check:
```python
def require_role(*allowed: Role):
    def dep(user=Depends(current_user)):
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep
```

Best practices:
- Default deny.
- Keep role matrix in one source file.
- Add role-based API tests on sensitive routes.

Pitfalls:
- Frontend-only authorization.
- Scattered role checks.

## Gate 4: Audit System

Objective: Create operational accountability.

Track:
- ticket changes
- inventory changes
- pricing edits
- loaner activity
- technician actions
- status transitions

Suggested table: activity_logs
- id
- user_id
- entity_type
- entity_id
- action
- old_value
- new_value
- created_at

Deliverables:
- Audit architecture
- Logging strategy
- Middleware hooks
- Audit helper utilities

Reasoning:
- Accountability and dispute resolution.

Tradeoffs:
- Extra write overhead.
- Requires retention strategy.

Migration strategy:
1. Start with ticket status, pricing, loaner transitions, inventory movements.
2. Expand to admin/settings edits.

Scalability impact:
- Enables forensic debugging and compliance posture.

Example:
```python
audit.log(
  actor_user_id=user.id,
  entity_type="ticket",
  entity_id=ticket.id,
  action="status_changed",
  old_value={"status": old},
  new_value={"status": new},
  request_id=req_id
)
```

Pitfalls:
- Logging in routes instead of services.
- Oversized payloads in old/new snapshots.

## Gate 5: Internal Event System

Objective: Create lightweight event-driven extensibility.

Examples:
- ticket_created
- ticket_closed
- inventory_low
- donor_harvested
- loaner_overdue

Important:
- No Kafka
- No microservices
- No overengineered messaging

Use lightweight internal pub/sub.

Deliverables:
- Event dispatcher design
- Subscription pattern
- Typed event examples

Reasoning:
- Decouples workflows without service sprawl.

Tradeoffs:
- In-process events are not durable by default.
- Outbox may be needed later.

Migration strategy:
1. Start with synchronous in-process dispatcher.
2. Add outbox table when background jobs mature.

Scalability impact:
- Clean extensibility for jobs/integrations.

Example:
```python
@dataclass
class TicketClosed(Event):
    ticket_id: int
    actor_user_id: int
    closed_at: datetime

dispatcher.subscribe(TicketClosed, notification_handler)
dispatcher.publish(TicketClosed(...))
```

Pitfalls:
- Hiding business logic inside subscribers.
- Publishing before transaction commit.

## Gate 6: Background Jobs

Objective: Move expensive operations off request threads.

Use cases:
- notifications
- scheduled scans
- reporting
- overdue loaner checks

Recommended:
- Arq (preferred simplicity)
- or Celery

Deliverables:
- Job architecture
- Queue strategy
- Retry handling
- Scheduling examples

Reasoning:
- Keeps API latency low.

Tradeoffs:
- Adds Redis dependency.
- Needs idempotent jobs and retries.

Migration strategy:
1. Start with overdue loaner scan + notifications.
2. Add reporting and periodic maintenance.

Queue/retry strategy:
- Queues: critical, default, low
- Exponential backoff
- Dead-letter handling after max retries

Example:
```python
async def send_ready_for_pickup_notification(ctx, ticket_id: int):
    # idempotency check first
    ...
```

Pitfalls:
- Non-idempotent jobs.
- No failed-job visibility.

## Gate 7: Frontend Scalability

Objective: Prepare frontend for operational complexity.

Required tools:
- Server state: TanStack Query
- UI state: Zustand

Requirements:
- optimistic updates
- cache invalidation
- pagination
- reusable tables
- loading boundaries
- error boundaries

UX priorities:
- speed
- clarity
- dense information display
- keyboard efficiency
- minimal click depth

Add:
- keyboard shortcuts
- barcode scanning readiness
- global search architecture

Deliverables:
- Frontend architecture plan
- Query patterns
- State separation strategy
- Reusable table system

Reasoning:
- Reduces stale-state bugs and ad hoc fetch logic.

Tradeoffs:
- Query-key discipline needed.
- Team onboarding for cache invalidation patterns.

Migration strategy:
1. Convert one page at a time (queue, tickets, inventory first).
2. Preserve current UX behavior during refactor.

Scalability impact:
- Better performance and maintainability as screens grow.

Example:
```ts
const useTicket = (id: number) =>
  useQuery({
    queryKey: ["ticket", id],
    queryFn: () => api.getTicket(id),
    staleTime: 30_000,
  });
```

Pitfalls:
- Mixing server state into Zustand.
- Missing optimistic rollback.

## Gate 8: Inventory Intelligence

Objective: Expand inventory systems into a major platform feature.

Support:
- donor devices
- harvested parts
- reusable components
- movement history
- low-stock alerts
- technician usage tracking

Future goals:
- profitability analysis
- donor yield analytics
- repair economics
- technician efficiency metrics

Deliverables:
- Inventory architecture
- Movement ledger design
- Analytics-ready schema strategy

Reasoning:
- Inventory should drive profitability insight.

Tradeoffs:
- More schema and reporting complexity.

Migration strategy:
1. Ensure every stock mutation emits a movement record.
2. Build analytics read models after source-of-truth quality is stable.

Scalability impact:
- Enables forecasting and margin optimization.

Pitfalls:
- Analytics built on incomplete ledger data.
- No reconciliation path.

## Gate 9: File Storage

Objective: Prepare attachment systems properly.

Support:
- intake photos
- receipts
- signatures
- repair evidence

Important:
- Do not store blobs in DB.
- Use object storage abstraction.

Future-ready providers:
- Cloudflare R2
- S3-compatible storage

Deliverables:
- Upload architecture
- File metadata schema
- Storage abstraction layer

Reasoning:
- Keeps DB lean and scales storage independently.

Tradeoffs:
- More moving parts and security controls.

Migration strategy:
1. Implement provider abstraction.
2. Roll out to one entity first (tickets), then expand.

Scalability impact:
- Efficient attachment handling at scale.

Pitfalls:
- Public object access without signed URLs.
- Orphaned file cleanup not implemented.

## Gate 10: Testing

Objective: Prevent regression chaos.

Backend:
- pytest
- httpx

Test:
- workflows
- inventory edge cases
- role permissions
- audit generation
- pricing validation

Frontend:
- Vitest
- React Testing Library

Test:
- queue interactions
- intake flow
- state transitions
- permissions rendering

Deliverables:
- Testing strategy
- Folder structure
- Example tests
- Workflow test plans

Reasoning:
- Protects critical operational flows.

Tradeoffs:
- Ongoing test maintenance.

Migration strategy:
- Prioritize intake->close, loaners, inventory usage/harvest, pricing approvals, RBAC denies, audit log generation.

Scalability impact:
- Faster and safer refactoring velocity.

Pitfalls:
- Snapshot-heavy tests with weak behavior coverage.
- Missing negative permission tests.

## Gate 11: DevOps + Deployment

Objective: Prepare for deployment reliability.

Requirements:
- Docker
- docker-compose
- environment configs
- CI/CD

CI/CD pipeline:
- lint
- test
- build
- deploy

Target stack:
- Frontend: Vercel or Cloudflare Pages
- Backend: Railway, Render, or Fly.io
- Database: Neon or Supabase PostgreSQL
- Storage: Cloudflare R2

Deliverables:
- Docker setup
- Deployment strategy
- CI/CD examples
- Environment management strategy

Reasoning:
- Repeatable builds and predictable release quality.

Tradeoffs:
- Setup complexity and secret-management overhead.

Migration strategy:
1. CI first.
2. Staging deploy.
3. Production deployment after migration/test gates.

Scalability impact:
- Lower release risk and ops burden.

Pitfalls:
- Deploying without migration safeguards.
- Secret leakage in pipelines.

## Gate 12: Observability

Objective: Create production debugging visibility.

Add:
- structured logging
- centralized error handling
- request IDs
- Sentry-ready architecture

Deliverables:
- Logging architecture
- Error middleware
- Tracing strategy

Reasoning:
- Faster incident triage.

Tradeoffs:
- Higher log volume and retention planning.

Migration strategy:
1. request_id middleware + error handler
2. structured logs
3. Sentry integration hooks

Scalability impact:
- Required for stable multi-user operations.

Example log shape:
```json
{
  "ts": "2026-05-10T20:00:00Z",
  "level": "INFO",
  "request_id": "req_123",
  "user_id": 42,
  "action": "ticket_closed",
  "entity_id": 10092
}
```

Pitfalls:
- Unstructured print logging.
- Missing correlation in async jobs.

## Recommended Implementation Waves

Wave A (2-3 weeks):
1. Gate 1
2. Gate 2 foundation (ORM + Alembic baseline)
3. Gate 10 baseline test expansion

Wave B (2-3 weeks):
1. Gate 3 auth/RBAC core
2. Gate 4 audit core
3. Gate 12 request IDs + error middleware

Wave C (2-4 weeks):
1. Gate 5 events
2. Gate 6 jobs (Arq + Redis)
3. Gate 7 frontend query/state modernization

Wave D (2-4 weeks):
1. Gate 8 inventory intelligence
2. Gate 9 file storage
3. Gate 11 deployment hardening + CI/CD full gates

## Gate Exit Criteria Template

Use for every gate:
1. Architecture docs updated
2. New tests added and passing
3. Existing workflows unchanged in behavior
4. Performance baseline not regressed
5. Rollback plan documented
6. Operational runbook updated

## Immediate Next Actions in This Repo

1. Create ADRs for Gate 1 and Gate 2 decisions.
2. Add SQLAlchemy base + Alembic scaffold without replacing working routes yet.
3. Refactor one workflow end-to-end as reference:
   - ticket close
   - inventory consume
4. Add role model schema and auth middleware skeleton behind feature flag.
5. Add activity_logs table and service helper, wire to ticket status changes first.
