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

## Validation

- Frontend focused test: `npm run test -- src/pages/HoursPage.test.tsx` (pass)
- Frontend production build: `npm run build` (pass)

## Notes

- Backend storage remains unchanged (`hours_worked` numeric hours) for compatibility
- UX now avoids decimal points for technician-facing time entry and display
