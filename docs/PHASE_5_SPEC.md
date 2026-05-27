# Phase 5: Parts & Donor Devices Inventory

Technician hours and queue management are complete. Phase 5 adds parts inventory tracking, donor device lifecycle management, and low-stock alerts to enable technicians to log which parts were used in repairs and manage a physical parts stockroom.

## Objectives

1. **Parts Inventory API:** CRUD operations for parts (create, list, search, update stock level)
2. **Donor Device Management:** Track donor phones by harvest status and available parts
3. **Part Usage Tracking:** Log which parts were consumed in a repair action (enhancement to Phase 3 repair actions)
4. **Low-Stock Alerts:** Dashboard and inventory page alerts when stock falls below threshold
5. **Inventory Pages:** UI to view parts inventory, manage stock levels, track donors

## Database Schema

### New Tables

```sql
CREATE TABLE parts (
    id INTEGER PRIMARY KEY,
    part_number TEXT UNIQUE NOT NULL,
    part_name TEXT NOT NULL,
    device_compatibility TEXT, -- e.g., "E4610,E4810,LG Classic"
    category TEXT NOT NULL, -- "Battery", "Screen", "Charger", "Button", "Housing", "Donor", etc.
    supplier TEXT,
    cost REAL, -- cost to Tech Restore
    retail_price REAL, -- markup for resale (future)
    
    status TEXT NOT NULL DEFAULT 'In Stock', -- "In Stock", "Low Stock", "Ordered", "Backordered", "Discontinued", "Donor Only"
    quantity_on_hand INTEGER DEFAULT 0,
    quantity_ordered INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 5, -- low-stock threshold
    reorder_quantity INTEGER DEFAULT 10,
    
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE part_usage (
    id INTEGER PRIMARY KEY,
    repair_action_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity_used INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repair_action_id) REFERENCES repair_actions(id),
    FOREIGN KEY (part_id) REFERENCES parts(id)
);

CREATE TABLE donor_devices (
    id INTEGER PRIMARY KEY,
    device_identifier TEXT UNIQUE NOT NULL, -- e.g., "Donor-E4810-001"
    device_model TEXT NOT NULL, -- "E4810", "LG Classic", etc.
    
    status TEXT NOT NULL DEFAULT 'Available for Parts', 
    -- "Available for Parts", "Partially Harvested", "Fully Harvested", "Repairable Resale", "Retired/Discarded"
    
    condition_notes TEXT, -- "Broken screen but battery OK", "Water damage", etc.
    parts_harvested TEXT, -- JSON array of harvested part IDs: [1, 5, 12]
    parts_available TEXT, -- JSON array of parts still available: [2, 3, 4]
    
    acquisition_date TEXT, -- when donor was received
    retirement_date TEXT, -- when donor was retired or fully harvested
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Modified Tables

**repair_actions:**
- Add optional `part_id` field (FK to parts table) for quick lookup
- Or track via part_usage junction table for multi-part repairs

**tickets:**
- No schema changes; parts used are tracked via repair_actions â†’ part_usage

## API Endpoints

### Parts Management

**GET /api/parts/**
- List all parts
- Query params: `category`, `status`, `low_stock_only` (bool)
- Response: Array of part objects with id, part_name, quantity_on_hand, status, reorder_level

**GET /api/parts/{id}**
- Get part details
- Response: Full part object with supplier, cost, notes, device_compatibility

**POST /api/parts/**
- Create new part
- Request: part_number, part_name, category, cost, reorder_level, reorder_quantity, supplier (optional)
- Response: Created part object with id

**PUT /api/parts/{id}**
- Update part (stock level, status, notes, reorder_level)
- Request: Partial part object (any field can be updated)
- Response: Updated part object

**DELETE /api/parts/{id}**
- Soft delete a part (mark status as "Discontinued", do not actually delete rows)
- Response: 204 No Content

### Donor Devices

**GET /api/donors/**
- List all donor devices
- Query params: `status`, `device_model`
- Response: Array of donor device objects

**GET /api/donors/{id}**
- Get donor device details with parts_harvested and parts_available arrays

**POST /api/donors/**
- Create new donor device
- Request: device_model, device_identifier, condition_notes, acquisition_date
- Response: Created donor object with id

**PUT /api/donors/{id}**
- Update donor (status, parts_harvested, condition_notes)
- Request: Partial donor object
- Response: Updated donor object

**POST /api/donors/{id}/harvest**
- Mark a part as harvested from a donor
- Request: { part_id: int }
- Response: Updated donor object with updated parts_available and parts_harvested

### Part Usage (Repair Actions Enhancement)

**POST /api/repair-actions/{id}/parts**
- Log parts used in a repair action
- Request: { part_id: int, quantity_used: int }
- Response: Created part_usage object with id
- Side effect: Decrement `parts.quantity_on_hand`

**GET /api/repair-actions/{id}/parts**
- Get all parts used in a repair action
- Response: Array of part objects with quantity_used

**GET /api/parts/{id}/usage**
- Get usage history for a specific part (which tickets/repairs used it)
- Response: Array of usage records with ticket_id, repair_action_id, quantity_used, date

### Alerts & Reporting

**GET /api/inventory/low-stock**
- Get all parts below reorder_level
- Response: Array of low-stock part objects with quantity_on_hand, reorder_level, quantity_ordered

**GET /api/inventory/donors/available**
- Get donors currently available for parts harvesting
- Response: Array of donor objects with status "Available for Parts" or "Partially Harvested"

**GET /api/dashboard** (enhancement)
- Include low-stock alert count in dashboard summary
- New field: `low_stock_parts_count: int`

## Frontend Pages

### Inventory Page
- **Left panel:** Parts search and filter (by category, status, low-stock only)
- **Center panel:** Parts table with columns: part_number, part_name, quantity_on_hand, reorder_level, status, device_compatibility
  - Click part to view details, edit, or log usage
  - Color-code rows: yellow if low stock, red if backordered/discontinued
- **Right panel:** "Add Part" form and quick actions (mark as ordered, update stock)

### Donor Devices Page
- **Top:** List of donors grouped by status (Available, Partially Harvested, Fully Harvested, Retired)
- **Each donor card:** Model, condition_notes, parts_available count, parts_harvested count, acquisition_date
  - "Harvest Part" button to move a part from available to harvested
  - "Update Status" button to transition to next lifecycle state
- **Bottom:** Add new donor form (device_model, device_identifier, condition_notes)

### Low-Stock Alert Widget (on Dashboard)
- Show count of parts below reorder_level
- Link to inventory page filtered by low-stock
- Example: "âš ï¸ 3 parts low in stock"

### Repair Action Detail Enhancement
- In ticket detail, when viewing a repair action:
  - Show parts used (if any) in a "Parts Used" section
  - Option to add parts to the repair action (post-repair logging)
  - Displays cost impact of parts

## Business Rules

1. **Part Consumption:** When a part is logged as used in a repair, automatically decrement `quantity_on_hand` by the quantity used.
2. **Low Stock Alert:** When quantity_on_hand â‰¤ reorder_level, alert dashboard and inventory page.
3. **Backordered:** Parts with status "Backordered" cannot be logged as used (show warning, allow "Override" for emergencies).
4. **Donor Lifecycle:** Donors move through states: Available â†’ Partially Harvested â†’ Fully Harvested â†’ Retired. Cannot go backward.
5. **Donor Parts Availability:** A part can only be harvested once from a donor (part_id cannot be in both parts_harvested and parts_available).
6. **Part Deletion:** Do not hard-delete parts. Mark status as "Discontinued" and allow list/search to filter them out by default.

## Implementation Sequence

1. **Backend Schema:** Add parts, part_usage, donor_devices tables
2. **Backend Functions:** CRUD for parts, donors; part consumption tracking; low-stock query
3. **Backend Routes:** /api/parts/*, /api/donors/*, /api/repair-actions/{id}/parts, /api/inventory/*
4. **Pydantic Models:** PartCreate/Response, DonorCreate/Response, PartUsageCreate/Response, InventoryAlert
5. **Frontend Types:** Part, DonorDevice, PartUsage types in api/tickets.ts
6. **Inventory Page:** Parts list with filtering, add part form, stock update form
7. **Donors Page:** Donor list with harvest workflow, status transitions
8. **Dashboard Enhancement:** Low-stock alert count and link
9. **Repair Action Detail Enhancement:** Display parts used, add parts UI
10. **Validation & Docs:** Smoke tests, update IMPLEMENTATION_STATUS.md, add usage examples to API_REFERENCE.md

## Testing Scope

- Create parts with various statuses and categories
- Log parts used in repair actions and verify stock decrements
- Check low-stock alerts on inventory page and dashboard
- Create donor device, harvest parts, verify state transitions
- Test filtering and search by category, status, device_compatibility
- Verify backordered parts cannot be logged without warning/override
- Confirm part deletion is soft (status update, not row removal)

## Known Decisions & Tradeoffs

1. **No automated reordering:** Reorder quantities and dates are manual. In Phase 6+, add email/calendar reminders.
2. **Simple cost tracking:** cost and retail_price are static fields. Future: cost history, supplier contracts, pricing tiers.
3. **Donor parts are JSON arrays:** Simple approach for MVP. Future: normalize to a junction table (donor_parts) if complex queries needed.
4. **No barcode/serial tracking:** Part serial numbers not tracked in v1. Future: add QR codes, batch numbers.
5. **No expiration dates:** Batteries and adhesives may expire. Future: add expiration_date field and alerts.

## Success Criteria (End of Phase 5)

- âœ“ All parts CRUD endpoints working (npm run build, no TypeScript errors)
- âœ“ Parts can be logged as used in repair actions, stock decrements correctly
- âœ“ Low-stock alerts display on dashboard and inventory page
- âœ“ Donor device lifecycle (Available â†’ Harvested â†’ Retired) works end-to-end
- âœ“ Inventory and Donor pages render with filters and forms
- âœ“ Browser smoke tests: Create part â†’ log in repair â†’ verify stock â†’ check dashboard alert
- âœ“ IMPLEMENTATION_STATUS.md updated to mark Phase 5 complete
- âœ“ API_REFERENCE.md includes parts and donor endpoints with examples


