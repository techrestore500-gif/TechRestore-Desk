# 2026-06-02 - Hours Page Root-Cause Report

## Root Cause

The backend stores `technician_hours.hours_worked` as decimal hours (for example `1.3333333333` for 1:20). The Hours UI was changed to minute input, but production behavior still showed mixed or incorrect day totals because date handling and selected-day filtering were not robust enough against mixed date shapes (`YYYY-MM-DD` vs datetime-like strings) and browser date parsing quirks.

## Storage Model Confirmed

- Backend storage field: `technician_hours.hours_worked`
- Stored unit: decimal hours (`REAL`)
- API payload field for manual logging: `hours_worked`
- Frontend manual input now uses minutes and converts with `minutes / 60` before API submit

## What Was Wrong In Frontend

- Selected-day filtering compared raw `work_date` values directly; datetime-like date strings could bypass exact day matching.
- Date display used `new Date(value)` for date-only values, which can shift by timezone and make day history appear misleading.
- Calendar/day aggregation and latest-day discovery did not normalize incoming `work_date` values before grouping/comparison.

## Fixes Applied

- Added `normalizeWorkDate()` to coerce all work-date values to `YYYY-MM-DD` on the Hours page.
- Applied normalized dates in:
  - selected-day filtering
  - calendar per-day total aggregation
  - latest logged date auto-selection logic
- Switched date rendering to local date parsing via `parseIsoDate(normalizeWorkDate(value))` to avoid timezone drift from date-only strings.
- Kept one clear unit model:
  - user enters **minutes**
  - frontend converts to decimal hours
  - backend stores decimal hours
  - UI displays `H:MM`

## Formatter Behavior Verified

`formatHoursClock()` displays correctly:
- 60 minutes (1.0 hours) -> `1:00`
- 80 minutes (1.3333 hours) -> `1:20`
- 100 minutes (1.6667 hours) -> `1:40`
- 200 minutes (3.3333 hours) -> `3:20`

## Data Validation

Local database check (`data/tech_restore_desk.sqlite`) currently contains exactly the real imported hours rows and total:
- 2026-05-07 -> 1.5
- 2026-05-10 -> 3.3333333333
- 2026-05-13 -> 0.5
- 2026-05-14 -> 0.5
- 2026-05-24 -> 1.0
- 2026-05-25 -> 1.1666666667
- 2026-05-26 -> 2.0
- 2026-05-27 -> 1.3333333333
- 2026-06-01 -> 1.6666666667
- 2026-06-02 -> 1.0
- Total -> 14.0

No bogus test rows were found locally during this pass.

## Validation Run

- Frontend Hours page test: pass
- Frontend build (`npm run build`): pass
- Backend tests were not re-run in this pass because backend code was unchanged.
