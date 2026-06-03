# API Reference

All endpoints are relative to `http://127.0.0.1:8787/api` in development. Request and response bodies are JSON.

## Pricing Catalog

Dedicated pricing catalog endpoints are available under `/api/pricing/catalog`.

### Read endpoints
- `GET /api/pricing/catalog`
- `GET /api/pricing/catalog/brands`
- `GET /api/pricing/catalog/models`
- `GET /api/pricing/catalog/issue-types`
- `GET /api/pricing/catalog/repair-types`
- `GET /api/pricing/catalog/rules`
- `GET /api/pricing/catalog/suggest?brand=...&model=...&issue_type=...`

### Write endpoints
- `POST /api/pricing/catalog/brands`
- `PATCH /api/pricing/catalog/brands/{brand_id}`
- `POST /api/pricing/catalog/models`
- `PATCH /api/pricing/catalog/models/{model_id}`
- `POST /api/pricing/catalog/issue-types`
- `PATCH /api/pricing/catalog/issue-types/{issue_type_id}`
- `POST /api/pricing/catalog/repair-types`
- `PATCH /api/pricing/catalog/repair-types/{repair_type_id}`
- `POST /api/pricing/catalog/rules`
- `PATCH /api/pricing/catalog/rules/{rule_id}`
- `DELETE /api/pricing/catalog/rules/{rule_id}`

Existing pricing calculator/default endpoints remain active:
- `POST /api/pricing/calculate`
- `GET /api/pricing/rules`
- `PATCH /api/pricing/rules`

## Health Check

### `GET /api/health`

Application health status. No authentication required. Used for startup verification.

**Response** (200):
```json
{
  "status": "ok",
  "database": "initialized"
}
```

---

## Customers

### `POST /api/customers`

Create a new customer.

**Request**:
```json
{
  "full_name": "John Doe",
  "primary_phone": "7325551234"
}
```

**Response** (201):
```json
{
  "id": 1,
  "full_name": "John Doe",
  "primary_phone": "7325551234",
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00"
}
```

### `GET /api/customers`

List all customers.

**Response** (200):
```json
[
  {
    "id": 1,
    "full_name": "John Doe",
    "primary_phone": "7325551234",
    "created_at": "2026-05-07T12:00:00",
    "updated_at": "2026-05-07T12:00:00"
  }
]
```

### `GET /api/customers/{id}`

Get a single customer by ID.

**Response** (200): Customer object (same as POST response).

**Error** (404): Customer not found.

### `PATCH /api/customers/{id}`

Update customer fields.

**Request** (any combination):
```json
{
  "full_name": "Jane Doe",
  "primary_phone": "7325555678"
}
```

**Response** (200): Updated customer object.

---

## Supported Models

### `GET /api/supported-models`

List all supported device models. Models are seeded once on startup and cannot be modified via API (design decision for v1).

**Response** (200):
```json
[
  {
    "id": 1,
    "manufacturer": "Kyocera",
    "model_name": "E4610",
    "can_use_loaner": true
  }
]
```

---

## Tickets

### `POST /api/tickets`

Create a new repair ticket. Customer must already exist.

**Request**:
```json
{
  "customer_id": 1,
  "device_model_id": 1,
  "issue_category": "Broken screen",
  "customer_approval_limit": 50,
  "intake_staff": "Jane (front desk)"
}
```

**Response** (201):
```json
{
  "id": 1,
  "customer_id": 1,
  "device_model_id": 1,
  "issue_category": "Broken screen",
  "status": "New Intake",
  "customer_approval_limit": 50,
  "estimated_replacement_value": null,
  "intake_staff": "Jane (front desk)",
  "assigned_tech": null,
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00"
}
```

### `GET /api/tickets`

List all tickets with optional search.

**Query parameters**:
- `search` (optional): Search by ticket number, customer name, phone, issue, or model name (case-insensitive substring match).

**Response** (200):
```json
[
  { "id": 1, "status": "New Intake", ... }
]
```

### `GET /api/tickets/{id}`

Get a single ticket with full details including status history, notes, and repair actions.

**Response** (200):
```json
{
  "id": 1,
  "customer_id": 1,
  "device_model_id": 1,
  "issue_category": "Broken screen",
  "status": "New Intake",
  "customer_approval_limit": 50,
  "estimated_replacement_value": 100,
  "intake_staff": "Jane",
  "assigned_tech": "Bob",
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00",
  "history": [
    {
      "id": 1,
      "ticket_id": 1,
      "status": "New Intake",
      "changed_by": "Jane",
      "changed_at": "2026-05-07T12:00:00",
      "note": "Ticket created"
    }
  ],
  "notes": [
    {
      "id": 1,
      "ticket_id": 1,
      "content": "Customer says phone won't turn on",
      "created_by": "Bob",
      "created_at": "2026-05-07T12:15:00"
    }
  ],
  "repair_actions": [
    {
      "id": 1,
      "ticket_id": 1,
      "repair_category_id": 4,
      "category_name": "Screen/LCD Replacement",
      "action_description": "Screen assembly replacement",
      "status": "planned",
      "part_cost": 30,
      "labor_minutes": 60,
      "difficulty_level": 4,
      "risk_level": 3,
      "estimated_replacement_value": 120,
      "performed_by": "Bob",
      "calculated_price": 150,
      "created_at": "2026-05-07T12:30:00",
      "updated_at": "2026-05-07T12:30:00"
    }
  ]
}
```

### `PATCH /api/tickets/{id}`

Update ticket fields (device model, issue, approval limit, assigned tech, replacement value, etc.).

**Request** (any combination):
```json
{
  "device_model_id": 2,
  "issue_category": "Broken screen and water damage",
  "customer_approval_limit": 75,
  "estimated_replacement_value": 120
}
```

**Response** (200): Updated ticket object.

### `PATCH /api/tickets/{id}/status`

Update ticket status. Records status change in history.

**Request**:
```json
{
  "status": "In Repair",
  "changed_by": "Bob",
  "note": "Started screen replacement"
}
```

**Response** (200): Updated ticket object.

**Error** (400): Invalid status or business rule violation.

### `POST /api/tickets/{id}/notes`

Add a note to a ticket.

**Request**:
```json
{
  "content": "Customer says phone was dropped from 6 feet",
  "created_by": "Jane"
}
```

**Response** (201):
```json
{
  "id": 1,
  "ticket_id": 1,
  "content": "Customer says phone was dropped from 6 feet",
  "created_by": "Jane",
  "created_at": "2026-05-07T12:00:00"
}
```

### `GET /api/tickets/{id}/notes`

List all notes on a ticket (included in ticket detail GET, but can be fetched separately if needed).

**Response** (200): Array of note objects.

### `POST /api/tickets/{id}/close`

Close a ticket. Validates that no loaner is still checked out.

**Request**:
```json
{
  "closed_by": "Bob",
  "final_price": 150,
  "closeout_note": "Screen replaced, tested and working"
}
```

**Response** (200): Updated ticket object with status "Picked Up / Closed".

**Error** (400): Ticket has active loaner or other validation failure.

### `POST /api/tickets/{id}/repair-actions`

Add a repair action (logged work) to a ticket. Validates that the repair category is not soldering-required.

**Request**:
```json
{
  "repair_category_id": 4,
  "action_description": "Screen assembly replacement",
  "part_cost": 30,
  "labor_minutes": 60,
  "difficulty_level": 4,
  "risk_level": 3,
  "estimated_replacement_value": 120,
  "performed_by": "Bob"
}
```

**Response** (201):
```json
{
  "id": 1,
  "ticket_id": 1,
  "repair_category_id": 4,
  "category_name": "Screen/LCD Replacement",
  "action_description": "Screen assembly replacement",
  "status": "planned",
  "part_cost": 30,
  "labor_minutes": 60,
  "difficulty_level": 4,
  "risk_level": 3,
  "estimated_replacement_value": 120,
  "performed_by": "Bob",
  "calculated_price": 150,
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00"
}
```

**Error** (400): Soldering-required category or other validation error.

### `GET /api/tickets/{id}/repair-actions`

List all repair actions on a ticket (included in ticket detail GET).

**Response** (200): Array of repair action objects.

### `GET /api/tickets/{id}/loaner-agreement`

Get the most recent loaner checkout payload for a ticket, enriched for print-friendly agreement output.

**Response** (200):
```json
{
  "id": 5,
  "ticket_id": 14,
  "ticket_number": "TR-00014",
  "customer_id": 2,
  "customer_name": "Loaner Customer",
  "customer_phone": "555-4444",
  "device_label": "iPhone 13",
  "issue_category": "Screen",
  "loaner_phone_id": 3,
  "loaner_code": "L-0003",
  "loaner_device_label": "Apple iPhone 8",
  "date_out": "2026-05-10T17:20:00.000000+00:00",
  "expected_return_date": "2026-05-17T17:20:00.000000+00:00",
  "condition_out": "Clean with minor wear",
  "charger_included": true,
  "sim_moved": true,
  "outgoing_call_tested": true,
  "incoming_call_tested": true,
  "deposit_amount": 50.0,
  "agreement_signed": true,
  "checkout_staff": "Alex",
  "status": "Checked Out"
}
```

**Error** (404): No loaner agreement found for the ticket.

---

## Loaners

### `POST /api/loaners`

Create a new loaner phone.

**Request**:
```json
{
  "model_id": 1,
  "imei": "123456789012345",
  "serial_number": "ABC12345"
}
```

**Response** (201):
```json
{
  "id": 1,
  "model_id": 1,
  "imei": "123456789012345",
  "serial_number": "ABC12345",
  "status": "Available",
  "checked_out_by": null,
  "checked_out_at": null,
  "deposit_amount": 100,
  "deposit_paid": false,
  "created_at": "2026-05-07T12:00:00",
  "updated_at": "2026-05-07T12:00:00"
}
```

### `GET /api/loaners`

List all loaners with current status.

**Response** (200):
```json
[
  {
    "id": 1,
    "status": "Available",
    "model_id": 1,
    "model_name": "Kyocera E4610",
    "checked_out_by": null,
    "checked_out_at": null,
    "deposit_paid": false,
    "is_overdue": false
  }
]
```

### `GET /api/loaners/{id}`

Get a single loaner with full details.

**Response** (200): Loaner object (same as POST response).

### `POST /api/loaners/{id}/checkout`

Check out a loaner to a customer/ticket.

**Request**:
```json
{
  "ticket_id": 1,
  "checked_out_by": "Jane",
  "deposit_amount": 100,
  "deposit_paid": true
}
```

**Response** (201): Updated loaner object with status "Checked Out".

**Error** (400): Loaner already checked out, ticket not found, etc.

### `POST /api/loaners/{id}/return`

Return a loaner.

**Request**:
```json
{
  "ticket_id": 1,
  "returned_by": "Jane",
  "condition_notes": "Device returned in good condition"
}
```

**Response** (200): Updated loaner object with status "Available".

**Error** (400): Loaner not checked out, ticket mismatch, etc.

---

## Dashboard

### `GET /api/dashboard/summary`

Quick overview metrics: total tickets, by status, loaner alerts.

**Response** (200):
```json
{
  "total_tickets": 10,
  "by_status": {
    "New Intake": 3,
    "Needs Diagnosis": 2,
    "In Repair": 2,
    "Ready for Pickup": 2,
    "Picked Up / Closed": 1
  }
}
```

### `GET /api/dashboard/alerts`

Loaner alerts: overdue, low deposit, not returned.

**Response** (200):
```json
{
  "overdue_count": 2,
  "active_count": 5,
  "overdue_details": [
    {
      "id": 1,
      "ticket_id": 5,
      "model_name": "Kyocera E4610",
      "checked_out_at": "2026-04-28T10:00:00",
      "days_overdue": 9
    }
  ]
}
```

---

## Pricing

### `POST /api/pricing/calculate`

Calculate repair price based on formula. Returns warnings if applicable.

**Request**:
```json
{
  "ticket_id": 1,
  "repair_category_id": 4,
  "part_cost": 30,
  "labor_minutes": 60,
  "difficulty_level": 4,
  "risk_level": 3,
  "estimated_replacement_value": 120
}
```

**Response** (200):
```json
{
  "ticket_id": 1,
  "repair_category_id": 4,
  "category_name": "Screen/LCD Replacement",
  "part_cost": 30,
  "labor_cost": 100,
  "difficulty_multiplier": 1.5,
  "risk_multiplier": 1.2,
  "total_before_adjustment": 216,
  "diagnostic_fee": 0,
  "rush_fee": 0,
  "discount": 0,
  "customer_price": 150,
  "warnings": [
    {
      "type": "replacement_value",
      "message": "Estimated repair cost ($150) is 62.5% of device replacement value ($120). Consider recommending replacement."
    }
  ]
}
```

**Warnings** (business rule enforcement):
- `approval_limit`: Repair cost exceeds customer approval limit.
- `replacement_value`: Repair cost is >60% of replacement value.
- `soldering_required`: Category requires soldering (not supported in v1).

### `GET /api/pricing/rules`

Fetch current pricing formula rules and defaults.

**Response** (200):
```json
{
  "defaults": {
    "base_labor_rate_per_hour": 90,
    "minimum_labor_charge": 20,
    "part_markup_percent": 0.35,
    "diagnostic_fee": 15
  },
  "difficulty_multipliers": {
    "1": 1,
    "2": 1.15,
    "3": 1.3,
    "4": 1.5,
    "5": 1.75
  },
  "risk_multipliers": {
    "1": 1,
    "2": 1.1,
    "3": 1.2,
    "4": 1.35,
    "5": 1.5
  },
  "repair_categories": [
    {
      "id": 1,
      "name": "Battery",
      "description": "Battery replacement",
      "default_policy": "Standard",
      "requires_soldering": 0
    }
  ]
}
```

### `PATCH /api/pricing/rules`

Update persisted pricing defaults used by `/api/pricing/rules` and as fallback defaults in `/api/pricing/calculate`.

**Request**:
```json
{
  "base_labor_rate_per_hour": 95,
  "diagnostic_fee": 25
}
```

All fields are optional; omitted fields keep existing values.

**Response** (200):
```json
{
  "defaults": {
    "base_labor_rate_per_hour": 95,
    "minimum_labor_charge": 20,
    "part_markup_percent": 0.35,
    "diagnostic_fee": 25
  }
}
```

### `GET /api/repair-categories`

List repair categories used by settings and pricing workflows.

**Query parameters**:
- `include_inactive` (optional, default false): include disabled categories.

**Response** (200):
```json
[
  {
    "id": 1,
    "name": "Battery",
    "description": "Battery replacement",
    "default_policy": "Standard",
    "requires_soldering": false,
    "active": true
  }
]
```

### `POST /api/repair-categories`

Create a new repair category.

**Request**:
```json
{
  "name": "Face ID calibration",
  "description": "Sensor and camera alignment workflow",
  "default_policy": "Advanced",
  "requires_soldering": false
}
```

**Response** (201):
```json
{
  "id": 12,
  "name": "Face ID calibration",
  "description": "Sensor and camera alignment workflow",
  "default_policy": "Advanced",
  "requires_soldering": false,
  "active": true
}
```

### `PATCH /api/repair-categories/{id}`

Update a repair category (including enable/disable via `active`).

**Request**:
```json
{
  "active": false
}
```

**Response** (200):
```json
{
  "id": 12,
  "name": "Face ID calibration",
  "description": "Sensor and camera alignment workflow",
  "default_policy": "Advanced",
  "requires_soldering": false,
  "active": false
}
```

All fields are optional; omitted fields keep existing values.

### `GET /api/status-workflow`

Read the status transition matrix and workflow guardrails used by ticket status updates.

**Response** (200):
```json
{
  "transitions": {
    "New Intake": ["Needs Diagnosis"],
    "Needs Diagnosis": ["Diagnosed", "Not Repairable", "Returned Unrepaired"],
    "Diagnosed": ["Approved", "Customer Approval Needed", "Waiting for Parts", "Replaced Instead"]
  },
  "guardrails": {
    "enforce_no_active_loaner_for_ready_for_pickup": true,
    "enforce_no_active_loaner_for_closed_statuses": true,
    "enforce_final_price_for_ready_for_pickup": true,
    "enforce_final_price_for_closed_paid_statuses": true
  },
  "updated_at": "2026-05-10T18:40:00+00:00"
}
```

### `PATCH /api/status-workflow`

Update status transitions and/or guardrail toggles.

**Request**:
```json
{
  "guardrails": {
    "enforce_final_price_for_ready_for_pickup": false
  }
}
```

**Response** (200):
```json
{
  "transitions": {
    "New Intake": ["Needs Diagnosis"]
  },
  "guardrails": {
    "enforce_no_active_loaner_for_ready_for_pickup": true,
    "enforce_no_active_loaner_for_closed_statuses": true,
    "enforce_final_price_for_ready_for_pickup": false,
    "enforce_final_price_for_closed_paid_statuses": true
  },
  "updated_at": "2026-05-10T18:45:00+00:00"
}
```

---

## Technician Queue (Phase 4)

### `GET /api/queue`

List tickets grouped by status for technician workflow.

**Response** (200):
```json
{
  "New Intake": [
    { "id": 1, "customer": "John Doe", "issue": "Broken screen", ... }
  ],
  "Needs Diagnosis": [
    { "id": 2, "customer": "Jane Smith", "issue": "Not charging", ... }
  ],
  "Approval Needed": [],
  "Waiting for Parts": [],
  "Loaner Outstanding": []
}
```

---

## Hours (Phase 4)

### `POST /api/hours`

Log time entry for a technician/ticket.

**Request**:
```json
{
  "ticket_id": 1,
  "technician": "Bob",
  "date": "2026-05-07",
  "hours": 1.5,
  "note": "Screen replacement and testing"
}
```

**Response** (201):
```json
{
  "id": 1,
  "ticket_id": 1,
  "technician": "Bob",
  "date": "2026-05-07",
  "hours": 1.5,
  "note": "Screen replacement and testing",
  "created_at": "2026-05-07T12:00:00"
}
```

### `GET /api/hours`

List hours by date range and technician (optional filters).

**Query parameters**:
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `technician` (optional): Filter by technician name

**Response** (200):
```json
[
  {
    "id": 1,
    "ticket_id": 1,
    "technician": "Bob",
    "date": "2026-05-07",
    "hours": 1.5,
    "note": "Screen replacement"
  }
]
```

### `GET /api/hours/summary`

Aggregate hours by technician and date range.

**Query parameters**:
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `technician` (optional): Filter the summary down to one technician

**Response** (200):
```json
{
  "by_technician": {
    "Bob": 8.5,
    "Jane": 6.5
  },
  "total": 15,
  "date_range": {
    "start": "2026-05-01",
    "end": "2026-05-07"
  }
}
```

### `GET /api/hours/active`

Return the current active clock session for a technician, if one exists.

**Query parameters**:
- `technician` (required): technician name

**Response** (200):
```json
{
  "id": 4,
  "ticket_id": 12,
  "technician": "Mattis",
  "work_description": "Bench diagnostics",
  "clocked_in_at": "2026-05-10T09:00:00+00:00",
  "clocked_out_at": null,
  "status": "active",
  "created_at": "2026-05-10T09:00:00+00:00",
  "updated_at": "2026-05-10T09:00:00+00:00"
}
```

### `POST /api/hours/clock-in`

Start an active clock session for a technician.

**Request**:
```json
{
  "technician": "Mattis",
  "ticket_id": 12,
  "work_description": "Bench diagnostics"
}
```

**Response** (201):
```json
{
  "id": 4,
  "ticket_id": 12,
  "technician": "Mattis",
  "work_description": "Bench diagnostics",
  "clocked_in_at": "2026-05-10T09:00:00+00:00",
  "clocked_out_at": null,
  "status": "active",
  "created_at": "2026-05-10T09:00:00+00:00",
  "updated_at": "2026-05-10T09:00:00+00:00"
}
```

### `POST /api/hours/clock-out`

Close the active clock session for a technician and write the completed time into the hours log.

**Request**:
```json
{
  "technician": "Mattis",
  "ticket_id": 12,
  "work_description": "Bench diagnostics complete"
}
```

**Response** (200):
```json
{
  "session": {
    "id": 4,
    "ticket_id": 12,
    "technician": "Mattis",
    "work_description": "Bench diagnostics complete",
    "clocked_in_at": "2026-05-10T09:00:00+00:00",
    "clocked_out_at": "2026-05-10T10:15:00+00:00",
    "status": "completed",
    "created_at": "2026-05-10T09:00:00+00:00",
    "updated_at": "2026-05-10T10:15:00+00:00"
  },
  "hours_entry": {
    "id": 9,
    "ticket_id": 12,
    "technician": "Mattis",
    "date": "2026-05-10",
    "hours": 1.25,
    "note": "Bench diagnostics complete",
    "created_at": "2026-05-10T10:15:00+00:00",
    "updated_at": "2026-05-10T10:15:00+00:00"
  }
}
```

---

## Reports (Phase 6)

### `GET /api/reports/summary`

Aggregate created tickets, closed tickets, revenue, and hours for a date range.

**Query parameters**:
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `technician` (optional): technician name used to filter ticket, hours, and breakdown data
- `repair_category` (optional): repair category name used to filter ticket, action, and breakdown data

**Response** (200):
```json
{
  "date_range": {
    "start": "2026-05-10",
    "end": "2026-05-10"
  },
  "technician_filter": "Jordan",
  "repair_category_filter": "Screen Repair",
  "created_tickets_count": 3,
  "closed_tickets_count": 2,
  "total_revenue": 450.0,
  "average_closed_ticket_revenue": 225.0,
  "total_hours": 5.0,
  "revenue_per_hour": 90.0,
  "available_technicians": ["Alex", "Jordan"],
  "available_repair_categories": ["Battery", "Screen Repair"],
  "technician_breakdown": [
    {
      "technician": "Jordan",
      "total_hours": 5.0,
      "tickets_worked": 2,
      "closed_tickets_count": 2,
      "total_revenue": 450.0
    }
  ],
  "repair_category_breakdown": [
    {
      "repair_category": "Screen Repair",
      "action_count": 2,
      "ticket_count": 2,
      "total_final_price": 450.0
    }
  ]
}
```

---

## Inventory (Phase 5+)

### `GET /api/inventory/parts`

List parts with optional filters.

**Query parameters**:
- `category` (optional)
- `status` (optional)
- `low_stock_only` (optional, default false)

**Response** (200):
```json
[
  {
    "id": 7,
    "part_number": "AMZ-20260525-007",
    "part_name": "ForPro 99% Isopropyl Alcohol (32 Fl Oz)",
    "category": "Cleaning Chemicals",
    "status": "In Stock",
    "quantity_on_hand": 1,
    "reorder_level": 2,
    "cost": 11.99
  }
]
```

### `POST /api/inventory/parts`

Create a part record.

### `PATCH /api/inventory/parts/{part_id}`

Update editable part fields (status, stock metadata, notes, etc.).

### `POST /api/inventory/parts/{part_id}/adjust`

Apply stock delta and write a movement-ledger record.

**Request**:
```json
{
  "quantity_delta": -1,
  "movement_type": "consume",
  "reason": "Used in repair",
  "ticket_id": 14
}
```

### `GET /api/inventory/low-stock`

Returns parts at/below reorder threshold.

### `GET /api/inventory/movements`

Returns paginated movement ledger.

### `POST /api/inventory/reconciliation`

Create reconciliation record and optional adjustment.

### `GET /api/inventory/reconciliation`

List reconciliation records (optionally filtered by part).

### `GET /api/inventory/donors`

List donor devices (optional `status`, `device_model` filters).

### `POST /api/inventory/donors`

Create donor device.

### `PATCH /api/inventory/donors/{donor_id}`

Update donor metadata/status/parts arrays.

### `POST /api/inventory/donors/{donor_id}/harvest`

Mark a donor part as harvested.

**Request**:
```json
{
  "part_id": 7
}
```

### `POST /api/inventory/parts/usage`

Log part usage for a repair action and decrement inventory.

### `GET /api/inventory/repair-actions/{repair_action_id}/parts`

List parts used by a repair action.

### `GET /api/inventory/parts/{part_id}/usage`

List usage history for a part.

### `GET /api/inventory/purchases`

List inventory purchase batches with line items.

### `GET /api/inventory/purchases/{purchase_id}`

Get one purchase batch.

### `POST /api/inventory/purchases`

Create purchase batch and line items.

---

## Customer History

### `GET /api/customers/{customer_id}/tickets`

List all tickets for one customer (used by customer-history UI).

**Response** (200):
```json
[
  {
    "id": 3,
    "ticket_number": "TR-OPS-20260507-01",
    "customer_id": 3,
    "customer_name": "Yossi Weiss",
    "device_label": "Wonder phone",
    "issue_category": "Touchpad replacement",
    "status": "Picked Up / Closed",
    "payment_status": "unpaid",
    "final_price": 30.0
  }
]
```

---

## System Maintenance (Phase 6)

### `POST /api/system/backup`

Create a local SQLite backup file in the workspace backups directory.

**Response** (200):
```json
{
  "file_name": "backup-2026-05-10T17-30-00.000000+00-00.sqlite",
  "backup_path": "C:/Users/owner/Desktop/Tech Restore/tech-restore-desk/backups/backup-2026-05-10T17-30-00.000000+00-00.sqlite",
  "created_at": "2026-05-10T17:30:00.000000+00:00",
  "file_size_bytes": 409600
}
```

### `GET /api/system/export`

Download a JSON snapshot of all application tables.

**Response** (200):
- Content type: `application/json`
- Includes `Content-Disposition` attachment header for download filename

**Body shape**:
```json
{
  "exported_at": "2026-05-10T17:35:00.000000+00:00",
  "database_path": "C:/Users/owner/Desktop/Tech Restore/tech-restore-desk/data/tech_restore_desk.sqlite",
  "tables": {
    "customers": [],
    "repair_tickets": []
  }
}
```

### `GET /api/system/history`

List recent manual backup and export activity recorded by the local app.

**Response** (200):
```json
[
  {
    "activity_type": "backup",
    "file_name": "backup-2026-05-10T17-30-00.000000+00-00.sqlite",
    "created_at": "2026-05-10T17:30:00.000000+00:00",
    "file_size_bytes": 409600,
    "file_path": "C:/Users/owner/Desktop/Tech Restore/tech-restore-desk/backups/backup-2026-05-10T17-30-00.000000+00-00.sqlite"
  },
  {
    "activity_type": "export",
    "file_name": "tech-restore-export-2026-05-10T17-35-00.000000+00-00.json",
    "created_at": "2026-05-10T17:35:00.000000+00:00",
    "file_size_bytes": 18200,
    "file_path": null
  }
]
```

---

## Error Handling

All errors return JSON with a `detail` field:

```json
{
  "detail": "Ticket 999 not found"
}
```

**Status codes**:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Validation or business rule error
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Unexpected error (see server logs)

---

## Rate Limiting and Concurrency

**Current**: None. Single-machine assumption.

**Future** (Phase 7+): If moving to multi-user, add rate limiting per technician and optimistic locking on ticket updates.

---

## Versioning

**Current API version**: v0 (pre-release)

All endpoints are under `/api/` with no explicit version in the path. Breaking changes may occur without notice during Phase 0-4 development.

**Stable API**: Expected after Phase 4.
