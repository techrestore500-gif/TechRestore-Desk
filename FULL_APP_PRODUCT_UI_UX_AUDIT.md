# Full App Product/UI/UX Audit

Date: 2026-05-30
Scope: frontend routes/layout/pages/components/auth/api/hooks/styles + relevant backend route/service behavior + docs
Product context: local-first repair desk app optimized for fast front-desk and technician workflow

## 1. Executive Summary

Tech Restore Desk is functionally strong and already covers most core repair-desk jobs: quick intake, ticket lifecycle, queue, hours, voicemail, inventory, settings, invites, and print flows. The biggest product risk is not missing features; it is information architecture and density balance. The app currently feels like a broad operations console rather than a focused repair desk in daily use.

The primary UX issues are: too many first-level sidebar destinations, several very long pages (especially Settings and Ticket Detail), inconsistent component density between pages, and advanced modules (Loaners, Donors) sharing equal visual priority with core daily work. Core workflows are usable, but not yet as fast and low-friction as they should feel at a repair counter.

The biggest opportunities are: simplify navigation, compact high-volume pages (Tickets/Voicemail/Queue), split oversized screens into clear sub-areas, standardize form behavior/messages, and move advanced modules to secondary navigation. With these changes, the app can feel significantly cleaner and faster without major architecture rewrites.

## 2. Top 10 Highest-Impact Improvements

1. Reduce top-level nav count and create a Core vs Admin split.
Why it matters: daily tasks become faster to find; cognitive load drops every time the app opens.

2. Move Loaners and Donors out of primary nav into Advanced/Operations.
Why it matters: keeps MVP desk flow focused while preserving existing capability.

3. Rework Ticket Detail into sectioned, compact blocks with jump links.
Why it matters: this is a high-frequency page and currently requires too much vertical scanning.

4. Compact the Voicemail list into a true row/grid layout across breakpoints.
Why it matters: voicemail is triage work; speed and scanability are critical.

5. Split Settings into multiple route sections (Business, Communications, Workflow, System).
Why it matters: current single-page control center is powerful but overly long and hard to manage.

6. Add URL-synced filters/paging for Tickets/Queue/Reports.
Why it matters: browser back/forward and sharable states improve practical daily usage.

7. Standardize success/error/validation behavior across all forms.
Why it matters: users should always know what saved, what failed, and what needs correction.

8. Add stronger data freshness cues (last updated, refresh semantics, stale-state handling).
Why it matters: repair desk decisions depend on trustworthy real-time-ish state.

9. Improve destructive action safeguards (delete/archive/revoke paths).
Why it matters: prevents costly mistakes during high-throughput front-desk usage.

10. Align visual tokens and typography hierarchy across pages.
Why it matters: current design direction is good, but consistency gaps make screens feel uneven.

## 3. Navigation and Page Structure

Current route map is broad and mostly logical, but too flat:
- Core daily routes: Dashboard, New Repair, Tickets, Queue, Hours, Voicemail
- Operational routes: Inventory, Loaners, Donors
- Admin routes: Users/Invites, Settings, Account
- Utility routes: print pages and invite/login routes

What works:
- Route naming is mostly understandable.
- Print pages are correctly not in sidebar.
- Role-based hide for Users/Invites in navigation is implemented.

Issues:
- Sidebar has too many first-level items for a counter app.
- High-frequency work competes visually with less frequent/advanced modules.
- Account appears as peer nav item instead of profile utility destination.
- Some naming can be clearer in a shop context (for example, Users / Invites could be Team Access).

Recommendation:
- Keep top level to a compact core set: Dashboard, Intake, Tickets, Queue, Hours, Voicemail, Inventory.
- Move Loaners/Donors/Reports/Settings/Users into an Admin or Operations secondary grouping.
- Keep Account in profile card/menu, not in core primary nav.

Loaners/Donors IA recommendation here aligns with section 10: hide from primary nav now, keep functionality and routes.

## 4. Visual Design Audit

Overall direction is good: warm neutral-green palette, rounded controls, soft cards, and approachable tone suitable for local service desk work.

Strengths:
- Color language is generally consistent with practical, calm brand tone.
- Buttons are readable and generally hierarchy-consistent.
- Table and panel styling is serviceable and mostly legible.
- Status chips in key places support quick scanning.

Design issues observed:
- Inconsistent density: some pages are compact (Voicemail rows), others oversized and tall (Settings, portions of Ticket Detail).
- Heavy inline-style usage causes small visual drifts between pages.
- Sidebar hover/active states are strong but visual weight can overpower content area.
- Meta text and helper copy sizing varies enough to feel inconsistent.
- Some chips/buttons overuse pill styles where flat compact controls would improve information density.
- Empty/loading states are uneven in quality and consistency.

Per-issue options:
- Minimal fix: unify spacing and typography scale constants and apply to top 5 pages.
- Nicer fix: create shared semantic UI primitives (page header, metric tile, section card, compact row, form row).
- Best long-term fix: move from ad hoc inline styles to tokenized style system (CSS vars + composable utility objects/components) with density variants (comfortable/compact).

## 5. Workflow Audit

### Intake to Ticket
- Good: Quick intake form is direct and supports customer lookup.
- Friction: several fields still feel equally weighted when some are optional; form can be faster with progressive disclosure.
- Recommendation: keep current single-screen approach but collapse optional sections by default.

### Ticket triage and status movement
- Good: one-click status chips are fast and status workflow guardrails are enforced server-side.
- Friction: ticket detail is long; status and notes context compete for attention.
- Recommendation: split page into compact sections and add sticky quick nav.

### Voicemail callback processing
- Good: row action model, playback, notes, and status are present.
- Friction: row wrapping and expanded detail presentation still costs vertical space on narrow layouts.
- Recommendation: adopt fixed column strategy + expandable detail drawer.

### Hours and queue
- Good: present and useful for technician operations.
- Friction: queue assignment is inline but lacks confirmation/context for accidental changes; hours page is vertically long.
- Recommendation: compact controls and clear action confirmations.

### Admin/settings workflow
- Good: rich capability, Twilio setup status, templates, workflow controls.
- Friction: too much in one screen, mixed save models (localStorage + DB) can confuse expectations.
- Recommendation: split Settings into route sections and label persistence scope clearly per section.

## 6. Page-by-Page Audit

### Dashboard
- Current purpose: high-level service desk snapshot and quick ticket actions.
- Works well: clear metrics + quick access to new repair.
- Awkward: quick status chip cluster per ticket can be visually noisy.
- Design issues: panel density and spacing are not fully compact.
- Functionality issues: all-ticket fetch model can become heavy as data grows.
- Data accuracy issues: no explicit recency indicator for metrics.
- Recommended improvements: add timeframe selector, compact cards, and metric refresh timestamp.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Tickets
- Current purpose: searchable ticket list and navigation hub.
- Works well: DataTable with sorting, pagination, row actions, saved views.
- Awkward: page/filter state not URL-bound; saved view affordance is functional but cramped.
- Design issues: compactness is decent but action area can wrap awkwardly.
- Functionality issues: current query pattern fetches full list then filters client-side.
- Data accuracy issues: no visible stale/fresh indicator.
- Recommended improvements: adopt paged API path by default and sync filters to URL.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, optimize.

### Intake / New Ticket
- Current purpose: fast walk-in intake and ticket creation.
- Works well: practical field set and customer match workflow.
- Awkward: optional fields are equally prominent as critical fields.
- Design issues: section pacing can still feel long.
- Functionality issues: numeric fields (estimated charge) and phone formatting rely on weak client validation.
- Data accuracy issues: free-form text allows inconsistent entries.
- Recommended improvements: stricter validation + collapsible optional section + sensible defaults.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Ticket Detail
- Current purpose: complete ticket lifecycle operations.
- Works well: status updates, notes, payment summary, parts usage, timeline.
- Awkward: too much vertical scan for common tasks.
- Design issues: section composition lacks strong hierarchy for first-look actions.
- Functionality issues: per-action parts usage fetch pattern can be chatty.
- Data accuracy issues: status/note context can be missed due to length and repeated sections.
- Recommended improvements: section anchors, compact status rail, grouped action blocks, batched usage retrieval.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Queue
- Current purpose: grouped technician queue by status.
- Works well: status grouping and card readability.
- Awkward: assignment dropdown in card can cause accidental edits.
- Design issues: card spacing is large for high-volume queue use.
- Functionality issues: hardcoded status order and limited workflow controls.
- Data accuracy issues: no explicit assignment-change feedback beyond optimistic update.
- Recommended improvements: compact card rows, explicit assign confirmation/toast, URL-synced filter state.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Hours
- Current purpose: time tracking and summary.
- Works well: clock-in/out + manual adjustment and log table.
- Awkward: dense but vertically long with repeated controls.
- Design issues: could be tighter with stacked compact modules.
- Functionality issues: weak guardrails for invalid time combinations.
- Data accuracy issues: potential misentries from free text and minimal validation.
- Recommended improvements: stronger validation and compact, tabbed sections.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Reports
- Current purpose: summary metrics and breakdowns.
- Works well: baseline filter and summary cards.
- Awkward: feels secondary and sparse relative to nav priority.
- Design issues: visual hierarchy is plain and not insight-first.
- Functionality issues: no export and limited trend exploration.
- Data accuracy issues: date constraints and context messaging could be clearer.
- Recommended improvements: make reports secondary nav and add export/trend charts later.
- Priority: Low
- Keep/simplify/merge/hide/remove: Keep, move to secondary nav.

### Inventory
- Current purpose: parts operations, stock monitoring, movement visibility.
- Works well: broad capability including movements and purchase ledger.
- Awkward: page combines too many sub-tools in one long flow.
- Design issues: variable density across table/panels.
- Functionality issues: manual micro actions (+1/-1) are slow for large operations.
- Data accuracy issues: limited guardrails for reconciliation quality in UI.
- Recommended improvements: split into Inventory, Movements, and Purchasing tabs.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, split into sub-sections.

### Voicemail
- Current purpose: voicemail triage and callback workflow.
- Works well: compact intent, visible caller/called line, menu actions, expandable details.
- Awkward: row wrapping at certain widths and menu behavior on narrow layouts.
- Design issues: some labels consume unnecessary width (From:/Line:/Received:/Duration: text weight).
- Functionality issues: no batch actions or date quick-filters.
- Data accuracy issues: unknown caller/line display can be ambiguous without stronger fallback cues.
- Recommended improvements: see section 8 detailed layout recommendation.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, optimize heavily.

### Settings
- Current purpose: business, Twilio, workflow, templates, backup/export controls.
- Works well: extensive operational capability and setup status visibility.
- Awkward: very long single route with mixed persistence models.
- Design issues: section transitions are visually repetitive over long scroll.
- Functionality issues: broad action surface without enough guardrails or section-level save strategy clarity.
- Data accuracy issues: user can misunderstand what is local browser state versus persisted backend state.
- Recommended improvements: split route sections and tag each section as Local or Shared/Persisted.
- Priority: High
- Keep/simplify/merge/hide/remove: Keep, split.

### Twilio/Phone Settings (inside Settings)
- Current purpose: Twilio credentials, greeting, webhook config, setup diagnostics.
- Works well: readiness and callback URL visibility.
- Awkward: exposed account SID and long form with many fields in one vertical stack.
- Design issues: important test actions are buried.
- Functionality issues: no explicit test-call workflow button.
- Data accuracy issues: webhook/base URL mistakes can break recording visibility.
- Recommended improvements: add guided setup wizard and explicit test actions.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Users / Invites
- Current purpose: invite creation and lifecycle management.
- Works well: essential create/resend/revoke flow exists.
- Awkward: list lacks filtering and compact summary controls.
- Design issues: invite cards become long with repeated metadata.
- Functionality issues: no bulk ops.
- Data accuracy issues: status readability okay, but aging and expiry context can be clearer.
- Recommended improvements: add status filters + compact table mode + invite age chips.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Account/Profile
- Current purpose: profile details and password changes.
- Works well: simple and clear.
- Awkward: feels detached from auth/session status context.
- Design issues: form is plain but acceptable.
- Functionality issues: immediate logout after password change can feel abrupt without transition.
- Data accuracy issues: none major.
- Recommended improvements: add success redirect path and clear session message flow.
- Priority: Low
- Keep/simplify/merge/hide/remove: Keep.

### Login/Auth/Invite Pages
- Current purpose: login, invite resolve/accept, logged-in login state.
- Works well: invite acceptance and auth message handling are straightforward.
- Awkward: LoginState page is low-value as a dedicated destination.
- Design issues: auth pages are consistent visually.
- Functionality issues: cross-tab session sync is not implemented.
- Data accuracy issues: stale tab perception can occur after logout elsewhere.
- Recommended improvements: auto-redirect logged-in users away from /login, implement tab sync.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Loaners
- Current purpose: loaner lifecycle operations.
- Works well: full checkout/return capability exists.
- Awkward: ID-based operational forms are heavy and not front-desk-friendly.
- Design issues: three large forms before list context adds cognitive load.
- Functionality issues: search/discovery is weak; workflow feels admin-heavy.
- Data accuracy issues: manual ID entry raises risk of wrong-entity operations.
- Recommended improvements: convert to selection-driven workflows and hide by default from core nav.
- Priority: Medium
- Keep/simplify/merge/hide/remove: Hide from core nav now; keep module.

### Donors
- Current purpose: donor device part-harvest workflow.
- Works well: available/harvested distinction and part operations are functional.
- Awkward: operational complexity is high for MVP desk focus.
- Design issues: dense cards with many controls per donor row.
- Functionality issues: no strong quick-search/filtering for scale.
- Data accuracy issues: part-state operations can be error-prone without stronger guardrails.
- Recommended improvements: move to future/advanced area or merge under Inventory sub-section.
- Priority: Low (for core MVP flow)
- Keep/simplify/merge/hide/remove: Hide now; keep code; consider future merge into Inventory.

### Customer Detail
- Current purpose: customer contact/history view.
- Works well: ticket history and core details are accessible.
- Awkward: limited action affordances (primarily read-focused).
- Design issues: acceptable but can be more compact.
- Functionality issues: no edit path from this screen.
- Data accuracy issues: none major.
- Recommended improvements: add quick customer edit and copy actions.
- Priority: Low
- Keep/simplify/merge/hide/remove: Keep, simplify.

### Print Pages (Intake, Invoice, Loaner Agreement)
- Current purpose: print-friendly operational artifacts.
- Works well: clean print structure and back links.
- Awkward: limited inline edit context before print.
- Design issues: generally good for print purpose.
- Functionality issues: none major.
- Data accuracy issues: depends on source ticket data completeness.
- Recommended improvements: minor pre-print validation badges.
- Priority: Low
- Keep/simplify/merge/hide/remove: Keep.

## 7. Forms and Fields Audit

Global findings:
- Major forms are usable but overexpose optional fields and under-communicate required constraints.
- Validation copy is technically clear but not always workflow-friendly.
- Save/cancel patterns vary by page; some sections auto-refresh while others rely on user interpretation.

Key form improvements:
- Intake:
  - Keep required fields visible: customer, phone, device brand/model, issue.
  - Collapse optional notes and advanced billing until needed.
  - Enforce phone format normalization and numeric constraints on estimate.
- Loaners:
  - Replace raw ID entry with searchable selectors.
  - Group checkout and return as guided sub-steps.
- Donors:
  - Add search and compact batch action affordances.
- Settings:
  - Show persistence scope label on each section: Local browser vs Shared database.
  - Add section-level unsaved-change guardrails.
- Account/Auth:
  - Add password requirement helper text before submit.

Per-issue options:
- Minimal fix: tighter labels, required markers, consistent inline error copy.
- Nicer fix: field grouping with collapsible advanced sections.
- Best long-term fix: shared form schema + validation UI framework for all pages.

## 8. Voicemail Inbox Recommendation

User goal check:
- Compact rows: partially met.
- Visible caller number: met.
- Visible called line: met.
- Vertical ellipsis menu: met.
- Expand details/audio only when needed: met.
- Avoid giant cards: mostly met.

### Option A: Current Flex-Wrap Rows (improved labels only)
- Pros: lowest effort, preserves current structure.
- Cons: wrapping behavior remains inconsistent on medium/narrow widths.
- Verdict: acceptable temporary patch, not best.

### Option B: Fixed Grid Row + Expand Drawer (recommended)
- Row columns: Status | Caller | Line | Received | Duration | Play | Menu
- Behavior:
  - Single-line on desktop.
  - Controlled two-line compact grid on tablet.
  - Dense two-row layout on mobile with menu anchored safely.
- Expand area below row for audio + notes only when opened.
- Pros: best scan speed and stable density.
- Cons: moderate implementation effort.
- Verdict: best balance of speed, clarity, and maintainability.

### Option C: Split Pane List + Detail Panel
- Pros: very fast for high-volume triage on desktop.
- Cons: complex responsive behavior, less natural on mobile, larger redesign.
- Verdict: viable long-term, not necessary immediately.

Recommendation:
- Choose Option B now.
- Add quick filters (New, Listened, Done, Last 24h, Last 7d) and optional bulk actions (Mark visible as listened).

## 9. Auth/Session/Profile Recommendation

Current strengths:
- AuthGate enforces session and displays clear expiry message.
- Invite flow is in place and production-oriented.
- Role checks are used on sensitive endpoints.

Current problems:
- Cross-tab session synchronization is missing.
- LoginState route is low-value and can feel odd in back-navigation paths.
- Session UX around stale pages can still feel confusing in multi-tab use.
- Token-in-localStorage remains a risk profile concern (pragmatic but not ideal).

Best solution path:
- Step 1 (quick): add storage/BroadcastChannel session sync, auto-redirect logged-in users away from /login.
- Step 2 (medium): add pre-expiry warning + optional renew flow.
- Step 3 (long-term): evaluate httpOnly cookie architecture if threat model or deployment surface grows.

## 10. Loaners and Donors Recommendation

Strong recommendation:
- Loaners: Hide for now from primary sidebar, keep module active and accessible via secondary Operations/Advanced nav.
- Donors: Hide for now from primary sidebar, keep in code and move under Inventory/Advanced.

Rationale:
- Both modules are useful capabilities but currently make the product feel heavier than a focused repair desk.
- The current stated goals prioritize intake, ticket flow, voicemail callbacks, and smooth counter operation.
- Hiding from primary nav improves focus without losing existing implementation investment.

Decision matrix:
- Loaners: Hide for now (not remove).
- Donors: Hide for now (and likely future merge under Inventory advanced tools).
- Remove now: not recommended until usage data confirms no need.

## 11. Quick Wins

Under 1 hour candidates:
- Reduce sidebar top-level items by moving advanced modules into grouped section.
- Add URL query sync for Tickets page filters/page.
- Compact Ticket Detail hero + status area spacing.
- Implement voicemail quick filters (status + recent range).
- Normalize form helper/error text style across Intake, Loaners, Donors, Settings.
- Add persistence labels in Settings sections (Local or Shared).
- Add safer destructive confirmations where currently weak.

## 12. Medium Improvements

Focused work items:
- Split Settings into separate routes/sub-pages.
- Redesign Ticket Detail layout with jump links and compact modules.
- Refine Queue card density and assignment feedback.
- Inventory page split into tabs (Parts, Movements, Purchases, Reconciliation).
- Improve donor and loaner discovery/search and reduce ID-based workflows.
- Introduce shared reusable page-section components for visual consistency.

## 13. Bigger Product Decisions

Decisions to make before implementation:
- Is Loaners part of everyday desk MVP or an advanced workflow for some shops only?
- Is Donor tracking a current must-have or intentionally deferred operations feature?
- Should Reports stay first-class nav or remain in admin/secondary area?
- What is acceptable auth/session model for production threat profile (localStorage token vs stronger cookie/session pattern)?
- How much of Settings should be mutable in-app versus environment-driven and locked?

## 14. Suggested Implementation Phases

Phase 1: clean up nav/pages and obvious UI issues
- Introduce Core vs Advanced nav grouping.
- Move Loaners/Donors/Reports/Users/Settings into secondary grouping.
- Tighten global spacing and typography consistency.
- Add consistent empty/loading/error visual states.

Phase 2: improve voicemail/ticket/intake workflows
- Implement voicemail Option B layout.
- Compact and section Ticket Detail.
- Add intake progressive disclosure and stronger validation.
- URL-sync ticket filters and paging.

Phase 3: polish settings/reports/account
- Split Settings into route sections.
- Improve reports usability (filter context, export, trend visibility).
- Improve account/session messaging and login route behavior.

Phase 4: optional/future modules
- Reposition advanced modules under Operations/Advanced.
- Consider merging Donors under Inventory advanced tools.
- Add deeper automation and power-user capabilities after core flow polish.

## 15. Do Not Change Yet

Until explicit approval:
- Do not remove Loaners module code or backend endpoints.
- Do not remove Donors module code or backend endpoints.
- Do not alter auth model in ways that weaken protection.
- Do not change Twilio webhook authentication/public callback behavior.
- Do not expose secrets in frontend or docs.
- Do not add public signup.
- Do not do broad architecture rewrites before nav/workflow polish proves insufficient.
- Do not break existing working flows while adjusting density/IA.

---

Overall recommendation: proceed with a focused UX/IA optimization pass, not a rewrite. Preserve current functional breadth, reduce visual and navigational weight, and center the product around fast repair-desk operations first.