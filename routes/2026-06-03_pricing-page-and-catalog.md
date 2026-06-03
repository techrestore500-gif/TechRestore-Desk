# 2026-06-03 Pricing Page and Catalog

## Summary
Implemented a dedicated Pricing management surface and backend pricing catalog schema/API, then moved pricing administration responsibilities out of Settings.

## What Changed

### Frontend
- Added new page and route:
  - `/pricing`
- Added sidebar entry:
  - `Pricing`
- Added Shop Tools shortcut to Pricing from Operations.
- Added new API client module for catalog operations.
- Added optional intake suggestion helper:
  - fetches a suggested price rule using brand/model/issue-type inference
  - allows one-click fill of estimated charge
- Removed Settings-hosted pricing management UI and replaced with a link to the Pricing page.

### Backend
- Added pricing catalog tables and indexes:
  - brands, models, issue types, repair types, rules
- Added starter seed records from pricing spec sheet references.
- Added pricing catalog CRUD endpoints and suggestion endpoint.
- Kept existing pricing calculator/defaults endpoints intact.

## Validation
- Backend: `pytest app/tests/test_api.py -q` passed.
- Frontend: `npm run build` passed.

## Operational Impact
- Pricing ownership is now centralized in one place.
- Front desk/admin can manage price rules without entering Settings.
- Intake can quickly apply known estimate guidance when a catalog match exists.
