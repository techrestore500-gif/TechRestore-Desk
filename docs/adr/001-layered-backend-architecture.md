# ADR-001: Layered Backend Architecture

## Date
2026-05-10

## Status
Accepted

## Context

The current backend consolidates all database operations, business logic, and API routing into a single large module (`app/database.py`). This creates several challenges:

1. **Testability**: Business logic is tightly coupled to SQL operations, making unit testing difficult.
2. **Maintainability**: Changes to business rules require modifications across concerns (SQL, validation, routing).
3. **Scalability**: As features grow, a monolithic database module becomes harder to navigate and change.
4. **Concurrency**: Multi-user scenarios and complex transactions are harder to manage without clear service boundaries.

## Decision

Adopt a layered backend architecture with clear separation of concerns:

```
routes/          → HTTP handlers (input validation, response serialization)
services/        → Business logic (rules, calculations, workflows)
repositories/    → Data access (SQL queries, schema operations)
schemas/         → Pydantic models (request/response contracts)
models/          → Domain models (state definitions, enums)
core/            → Utilities (logging, errors, configuration)
```

### Route Layer
- Handle HTTP requests and responses
- Validate input using Pydantic schemas
- Delegate business logic to services
- Catch and translate errors to HTTP responses

### Service Layer
- Encapsulate business logic
- Coordinate between repositories
- Handle state transitions and validations
- Implement domain rules (pricing, status transitions, guards)

### Repository Layer
- Manage all database operations
- Execute SQL queries
- Return domain objects
- Handle transactions at this level for multi-step operations

### Schema Layer
- Define Pydantic request/response models
- Enforce type safety
- Document API contracts

### Models Layer
- Define enums for controlled values (TicketStatus, Priority)
- Define data classes for domain objects
- Separate from database schema

## Consequences

### Positive
- **Testability**: Services can be tested without database.
- **Clarity**: Business logic is isolated and easier to understand.
- **Reusability**: Services can be called from multiple routes or background jobs.
- **Flexibility**: Repository implementation can change (SQLite → PostgreSQL) without affecting services.
- **Concurrency**: Clear transaction boundaries at repository level.

### Negative
- **Initial overhead**: Requires more files and structure.
- **Indirection**: More layers means more files to navigate.
- **Coordination**: Changes spanning layers require edits in multiple places.

## Alternatives Considered

1. **Keep monolithic database module**: Faster short-term, but scales poorly.
2. **Full domain-driven design (DDD)**: More ceremony than needed for current scale; revisit if SaaS grows.
3. **Anemic model + managers**: Service-locator pattern; less explicit than layered architecture.

## Adoption Timeline

- **Phase 1**: Migrate ticket, pricing, and customer domains to new structure.
- **Phase 2**: Migrate loaner, inventory, and hours domains.
- **Cleanup**: Remove legacy code from monolithic module.

## References

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture - Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
