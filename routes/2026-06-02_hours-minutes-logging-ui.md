# 2026-06-02 - Hours Logging Uses Minutes

## Goal

Stop logging and showing technician time in decimal-hour points (for example `1.25`, `2.5`) and use minute-based UX instead.

## Delivered

- Updated manual hours logging input on the Hours page from decimal hours to whole minutes
- Converted minute input to backend-compatible hours during submit (`minutes / 60`)
- Updated validation messaging to require positive whole minutes
- Updated elapsed active-session display to hour/minute format
- Updated selected-day total display to hour/minute format
- Updated day history row display to hour/minute format
- Updated all hour/minute displays to clock notation (`H:MM`) so values appear as `2:15` instead of decimal notation like `2.25`
- Updated Hours page test expectation for new total label format
- Fixed day-history visibility by switching default "today" date generation to local calendar date instead of UTC ISO slicing
- Added first-load fallback behavior: when the initially selected day has no entries, the page now auto-selects the most recent logged work date so existing logs are visible immediately
- Improved empty-state guidance to clarify that history is date-filtered and can be viewed by changing the calendar day
- Reworked Hours page data loading to month-range queries so the calendar can display real per-day hour totals in each date cell
- Added day-cell totals (`H:MM`) directly inside calendar cells for days with logged time
- Corrected selected-day total logic to sum only selected-day entries (instead of using month summary totals)
- Added visible-month total summary card with explicit start/end range display
- Applied technician filter to month hours and month summary queries so Mattis filtering remains accurate
- Hardened backend hours date handling: write path now normalizes `work_date` to `YYYY-MM-DD` and list/summary filters now use SQLite `DATE(work_date)` comparisons to include legacy datetime-like rows
- Added backend regression test coverage for datetime-like `work_date` filtering compatibility

## Validation

- Frontend focused test: `npm run test -- src/pages/HoursPage.test.tsx` (pass)
- Frontend production build: `npm run build` (pass)
- Backend focused tests: `python -m pytest app/tests/test_api.py -k Hours` (pass)
- Local imported-hours verification query confirms expected rows including `2026-05-27 = 1.33` and total `14.0`

## Notes

- Backend storage remains unchanged (`hours_worked` numeric hours) for compatibility
- UX now avoids decimal points for technician-facing time entry and display
