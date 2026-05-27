# Business Rules and Constraints

This document captures the business logic and constraints that guide the app's behavior. These rules are enforced in the backend and must be respected by any frontend or extension.

## Repair Workflow Rules

### Soldering Exclusion (Fundamental Constraint)

**Rule**: No standard soldering workflow in v1. The following repair categories are not supported for normal technician flow:
- Charging Port Replacement (requires soldering on S2720 and Cadence models)
- Microphone Replacement (requires soldering)

**Enforcement**:
- In `app/database.py`, repair categories are seeded with `requires_soldering = true/false` flag.
- When adding a repair action via `POST /api/tickets/{id}/repair-actions`, the API checks this flag.
- If a technician attempts to add a soldering-required action, the request is rejected with `400 Bad Request` and error message: "Soldering-required repair categories are not supported in v1 workflow."

**Implication for Technician**:
- If customer needs charging port or microphone repair, technician must:
  1. Mark the ticket as "Not Repairable" or create an external quote.
  2. Do not attempt to add a repair action for these categories.

**Future Handling** (Phase 7+):
- Consider "Outsource/Vendor" status for repairs that Tech Restore doesn't perform.
- Track external quotes and referrals separately.

---

## Approval and Pricing Rules

### Approval Limit

**Rule**: Every ticket has a `customer_approval_limit` (in dollars). Technician cannot proceed with repair without explicit customer approval if cost exceeds limit.

**Enforcement**:
- Pricing calculation (`POST /api/pricing/calculate`) emits a `approval_limit` warning if estimated repair price â‰¥ 95% of approval limit.
- Warning message: "Repair cost ($X) approaches or exceeds customer approval limit ($Y). Get explicit approval before proceeding."
- The warning is *informational*; the API does not block the technician from proceeding.
- Technician must call customer and update approval limit or status to "Customer Approval Needed".

**Best Practice**:
1. Check approval limit upfront during intake.
2. If diagnosis cost is high, confirm customer can approve repairs up to that range.
3. If cost exceeds limit during repair planning, update ticket status and call customer.

---

### Replacement Value Warning

**Rule**: If estimated repair cost exceeds 60% of device replacement value, recommend replacement instead of repair.

**Enforcement**:
- Pricing calculation emits a `replacement_value` warning if `repair_cost > 0.6 * estimated_replacement_value`.
- Warning message: "Repair cost ($X) is 62.5% of device replacement value ($Y). Consider recommending replacement to customer."
- The warning is *informational*; the API does not block the repair.

**Business Reason**: 
- Customers often don't realize it's cheaper/better to replace an old device than repair it.
- Warning helps technicians make customer-friendly recommendations.
- Tech Restore preserves goodwill by suggesting replacement when it makes financial sense.

**Action**:
1. If warning appears, discuss replacement option with customer.
2. If customer wants repair anyway, update `estimated_replacement_value` on ticket if needed.
3. If customer chooses replacement, update ticket status to "Replaced Instead" and close.

---

### Soldering in Pricing Context

**Rule**: Pricing calculation should warn (but not error) if a pricing request includes a soldering-required category.

**Enforcement**:
- In `POST /api/pricing/calculate`, if `repair_category_id` refers to a soldering-required category, include a `soldering_required` warning.
- Warning message: "This repair category requires soldering, which is not supported in the v1 workflow."
- The warning is *informational* during estimation; however, the actual repair action cannot be added later (see "Soldering Exclusion" above).

**Implication**:
- Technician can estimate cost for informational purposes (e.g., to quote customer).
- But if technician tries to log the repair action, the API rejects it.

---

## Loaner Rules

### Loaner Checkout

**Rule**: A loaner can only be checked out to one ticket at a time. Once checked out, it is no longer available for other customers.

**Enforcement**:
- Loaner `status` must be "Available" to checkout.
- On checkout, status becomes "Checked Out".
- Attempting to checkout an already-checked-out loaner returns `400 Bad Request`.

### Loaner Return and Ticket Close

**Rule**: A ticket *cannot* be closed if a loaner is still checked out to it.

**Enforcement**:
- `POST /api/tickets/{id}/close` checks if any loaner is checked out to this ticket.
- If yes, error: "Cannot close ticket with active loaner. Return loaner first."
- Technician must return loaner before closing ticket.

**Workflow**:
1. Technician finishes repair.
2. Technician returns loaner (deposits refunded, status â†’ "Available").
3. Technician closes ticket (final price, closeout notes, status â†’ "Picked Up / Closed").

### Loaner Overdue

**Rule**: A loaner is overdue if it's been checked out for more than 7 days (configurable).

**Enforcement**:
- `is_overdue` flag is computed in `GET /api/loaners` and `GET /api/dashboard/alerts` based on `days_checked_out > 7`.
- No automatic action; it's an alert for staff to follow up with customer.

**Alert Display**:
- Dashboard shows count of overdue loaners.
- Dashboard alerts include details: loaner model, customer, days overdue.

---

## Ticket Status Lifecycle

### Valid Status Transitions

```
New Intake
  â†“ (diagnosis / quick fix)
Needs Diagnosis
  â†“ (diagnosis complete)
Diagnosed
  â†“ (awaiting customer approval)
Customer Approval Needed
  â†“ (customer approves)
Approved
  â†“ (waiting for parts or ready to repair)
Waiting for Parts  OR  Ready for Repair
  â†“ (repair in progress)
In Repair
  â†“ (repair complete, ready for pickup)
Ready for Pickup
  â†“ (customer picks up, paid)
Picked Up / Closed
```

**Alternative paths**:
- `New Intake` â†’ `Not Repairable` (device cannot be fixed).
- `Customer Approval Needed` â†’ `Customer Declined` (customer doesn't approve).
- Any status â†’ `Returned Unrepaired` (e.g., customer changes mind, returns device before repair).

**Enforcement**:
- Currently, *any* status can transition to *any* other status (no validation).
- **Future**: Add state machine validation in Phase 4 to prevent invalid transitions.

---

## Device and Repair Category Rules

### Supported Device Models

**Rule**: Only devices in the `supported_models` table can be repaired via the intake workflow.

**Enforcement**:
- On intake, frontend fetches supported models and shows them in a dropdown.
- Backend validates `device_model_id` exists in database.
- Attempting to create a ticket with invalid `device_model_id` returns `400 Bad Request`.

**Supported Devices** (seeded):
- Kyocera E4610
- Kyocera S2720
- Kyocera KX414
- ... (see `app/seed.py`)

**Adding a Device** (v1):
- Manually add to `app/seed.py` in `supported_devices` list.
- Restart backend (deletes and reinitializes database).

**Future** (Phase 7):
- Admin UI to add/modify supported devices without code change.

### Repair Categories

**Rule**: All repairs must map to a category in the `repair_categories` table.

**Categories** (seeded):
- Battery Replacement
- Charging Port Cleaning
- Charging Port Replacement (requires soldering)
- Filter/Setup Support
- Hinge/Housing Repair
- Keypad/Button Repair
- Microphone Repair (requires soldering)
- SIM/Contact Transfer
- Screen/LCD Replacement
- Speaker/Earpiece Repair
- Water Damage Diagnostic

**Repair actions** logged via `POST /api/tickets/{id}/repair-actions` must reference a valid `repair_category_id`.

**Cannot Remove Categories**:
- Categories are seeded once and not exposed via edit API.
- Removing a category requires manual database edit or code change + restart.

---

## Pricing Rules

### Pricing Formula

Repair cost is calculated as:
```
labor_cost = labor_minutes / 60 * hourly_rate
base_cost = part_cost + labor_cost
difficulty_multiplier = 1.0 + (difficulty_level - 1) * 0.25  (range 1.0â€“2.0 for levels 1â€“5)
risk_multiplier = 1.0 + (risk_level - 1) * 0.20  (range 1.0â€“1.8 for levels 1â€“5)
subtotal = base_cost * difficulty_multiplier * risk_multiplier
customer_price = subtotal + diagnostic_fee + rush_fee - discount
```

**Defaults**:
- `hourly_rate` = $100
- `diagnostic_fee` = $0
- `rush_fee` = $0
- `discount` = $0

**Configurable Defaults**:
- Pricing defaults can be edited in `app/database.py` in the `calculate_pricing()` function.
- Technician can override per-repair via API request fields.

**Future** (Phase 7):
- Admin UI to configure defaults and rules without code change.

---

## Technician Queue Rules

**Rule**: Queue prioritizes repair workflow over diagnosis.

**Queue groupings** (in priority order):
1. **Loaner Outstanding** â€” customer has overdue loaner; highest priority.
2. **Waiting for Parts** â€” cannot proceed without parts; customer needs follow-up.
3. **Approval Needed** â€” customer must approve estimate; blocks repair.
4. **New Intake** â€” just arrived; needs triage and diagnosis.
5. **Needs Diagnosis** â€” awaiting technician review.
6. **In Repair** â€” actively being worked; not in queue (informational only).
7. **Ready for Pickup** â€” completed; customer awaiting pickup; not in queue.

**Technician Workflow**:
1. Open queue.
2. Start with "Loaner Outstanding" and "Waiting for Parts" items.
3. Then handle "Approval Needed" items (call/email customer).
4. Then diagnose and triage "New Intake" items.
5. Then work on "Needs Diagnosis" items.
6. Log hours for all work completed.

---

## Hours and Time Tracking

**Rule**: Hours are optional but recommended. Every repair action should ideally have time logged.

**Tracking**:
- Time entry can be added via `POST /api/hours` (Phase 4).
- Time can be attached to a ticket optionally (helps calculate technician productivity).
- Hours are reported by day, week, month for business analytics.

**Business Use**:
- Track technician utilization (hours worked vs. time available).
- Correlate hours with revenue (profit per billable hour).
- Identify bottlenecks (categories taking unexpectedly long).

---

## Data Retention and Privacy

**Rule**: No data is deleted. All records are kept for audit trail.

**Soft Deletes**:
- Customers and tickets are never hard-deleted.
- If a customer or ticket becomes irrelevant, update status or add a flag.
- Status history is immutable (append-only).

**Backups**:
- Database file is located at `tech-restore-desk/data/tech_restore_desk.sqlite`.
- Manual backup recommended daily (Phase 7 will add automated backup).

---

## Summary of Enforcement Points

| Rule | Enforced By | Severity |
|------|-------------|----------|
| No soldering repairs | API rejects repair action creation | Hard (400 error) |
| Approval limit check | Pricing calc emits warning | Soft (advisory) |
| Replacement value check | Pricing calc emits warning | Soft (advisory) |
| Loaner single-checkout | API checks status on checkout | Hard (400 error) |
| Cannot close with active loaner | API checks before close | Hard (400 error) |
| Valid device model | API validates on ticket create | Hard (400 error) |
| Valid repair category | API validates on action add | Hard (400 error) |
| Status history immutable | Database append-only | Hard (design) |

---

## Decision Log

### Why No Soldering?
- Soldering requires specialized equipment and skill.
- Risk of damage to board/components is high.
- Tech Restore's initial technician pool may not have soldering certification.
- Outsourcing these repairs to specialized vendors is safer and more profitable.

### Why Immutable History?
- Audit trail helps debug discrepancies (e.g., "Was this approved?").
- Immutability prevents accidental data loss.
- Simplifies reporting (no need to track change deltas).
- Supports business compliance if needed later.

### Why Single-Machine Design?
- Tech Restore operates one shop location with one technician present at a time.
- No need for multi-user concurrency.
- Simplifies development (no network, auth, sync issues).
- Reduces operational burden (no server to manage).
- Data stays on-premises (customer privacy).

---

## Future Considerations (Phase 5+)

- **Parts Inventory**: Track donor devices and parts inventory; alert when low.
- **Customer Communication**: Auto-generate SMS/email notifications for status updates.
- **Pricing Tiers**: Support multiple pricing profiles (rush, discount, warranty).
- **Analytics**: Real-time dashboard of revenue, hours, device models, repair success rates.
- **Integration**: Potential future integration with parts suppliers or shipping APIs.



