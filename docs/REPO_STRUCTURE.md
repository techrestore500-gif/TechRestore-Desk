# Repository Structure

## Purpose

This document defines the current top-level repository layout and where to place new artifacts.

## Top-level layout

- `backend/`: FastAPI service, data access, tests, and backend scripts
- `frontend/`: React + TypeScript app, routes, pages, and UI components
- `docs/`: Living source-of-truth documentation (architecture, status, deployment, implementation notes)
- `routes/`: Chronological implementation logs and feature/fix history entries
- `reports/`: Historical audit and pass reports grouped by domain
  - `reports/ux/`: UX audits and redesign pass reports
  - `reports/auth_and_access/`: auth/access investigations and recovery reports
  - `reports/operations/`: operations and persistence audits
  - `reports/voicemail/`: voicemail-focused UI/behavior reports
- `data/`: local SQLite and runtime local artifacts (ignored where applicable)
- `backups/`: local backup outputs

## Placement rules

- New architecture or implementation guidance belongs in `docs/`.
- Every feature/fix/update timeline note must be added to `routes/`.
- Report-style retrospectives and audits should be placed under `reports/` in the closest matching category.
- Avoid adding report markdown files back to repo root.
