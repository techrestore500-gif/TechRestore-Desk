# Product and Technical Decisions

This document captures key decisions from ANSWERS.md and design conversations that guide implementation and scope.

## Pricing & Revenue

**Diagnosis Fee:** No charge for diagnosis. Technician time is absorbed as overhead; customer commits to repair if approved.

**Loaner Deposit:** $50 per loaner device. All loaners must be the same model (cheap, low-cost device). Deposit is refundable on return.

**Free Services with Repair:** Screen replacement with any repair is free (included in labor/cost).

**Payment Methods:** Cash, check, credit card, possibly Zelle. Payment collection is out of scope for Phase 4; implement in Phase 6+ reporting and checkout.

**Parts Resale:** Out of scope for v1. Tech Restore may sell surplus parts or devices in future, but current focus is internal repair workflow.

**Referrals:** When repairs cannot be done (e.g., unsupported device, board-level work), provide customer with business cards of other repair shops. No formal referral tracking system needed yet.

## Pricing Override & Permissions

**Open Decision:** Who can override pricing approval limits? Who can close tickets?
- Current implementation: No role-based permissions yet (Phase 7+)
- Assumption: Single operator or trusted technician can override
- Design debt: Add permissions/audit log in Phase 7

## Device Support

**Primary Devices:**
- Kyocera E4610 (main flip)
- Kyocera E4810/E4811 (rugged flip)
- Kyocera S2720/Cadence (rugged flip)
- LG Classic (cost-effective)
- LG Exalt (niche)
- FIG/FIG Mini (battery/setup)
- F30/F52 (referenced in ANSWERS.md)
- TCL/eTalk (referenced in ANSWERS.md)

**Secondary/Future:**
- CAT S22 (smart-flip; can be time sink)
- Qin (setup/support-heavy)
- Wonder (collect real demand first)

**Constraints:**
- No soldering for S2720 charging port or microphone
- No board-level repair
- Screen/LCD is "Quote" for most devices (specialist assessment)
- Hinge/housing is "Quote" for most (complex work)

## Loaner Inventory

**Starter Fleet:**
- 3â€“5 basic flip loaners (low-cost devices)
- 2â€“3 Kyocera rugged loaners if available
- 1â€“2 LG Classic/Exalt loaners

**Loaner Duration:** 30 days max (enforced in close-ticket logic)

**Status Lifecycle:**
- Available â†’ Checked Out â†’ Returned Needs Reset/Cleaning â†’ Available
- Out-of-service: Damaged, Lost, Retired

## Parts Inventory Strategy

**First 30 Days:** Stock safe, common, low-cost items. Avoid overstocking.

**Must-Have Tools & Supplies:**
- Screwdrivers, pry tools, spudgers, tweezers, SIM tools
- Cleaning supplies, compressed air, adhesive tape
- Phone bags, labels, intake envelopes
- Cables (micro-USB, USB-C) and chargers

**Starter Parts (Phase 5+):**
- Kyocera E4810/E4811/E4830/E4831 batteries
- LG Classic/Exalt batteries
- FIG/FIG Mini batteries
- S2720 batteries
- Back covers and battery doors
- Donor devices (Kyocera rugged flips, LG Classic/Exalt)

**Part Statuses:**
- In Stock
- Low Stock
- Ordered
- Backordered
- Discontinued
- Donor Only (harvested from donor devices)

**Donor Phone Statuses:**
- Available for Parts
- Partially Harvested
- Fully Harvested
- Repairable Resale
- Retired/Discarded

## Technical Decisions

**Backend:** Local web app (no cloud, no authentication).

**Database:** SQLite (immutable history, soft deletes, audit trails via created_at/updated_at).

**Photos/Diagnostics:** Not needed for v1. Focus on text-based intake and notes.

**Backup & Cloud:** No automated cloud sync or backup urgently needed. Local .sqlite file is the source of truth.

**Carrier Tracking:** No carrier information tracked (all devices are unlocked or SIM-agnostic flip phones).

## Scope Boundaries (Out of Phase 4)

- Payment processing and checkout UI (Phase 6+)
- Role-based permissions and override audit trails (Phase 7)
- Automated backup, cloud sync, or export workflows (Phase 6+)
- Parts selling/inventory marketplace (future)
- Device refurbishment resale tracking (future)
- Multi-location support (future)
- Customer self-service portal (future)

## Validation Notes

These decisions are tested against the first 30â€“90 days of real usage. Expect to revise:
- Device support list (add/remove based on demand)
- Parts stock list (trim slow-movers, add fast-movers)
- Pricing multipliers and labor rates (based on actual time tracking from Phase 4 hours log)
- Loaner deposit amount or fleet size (based on real checkout patterns)


