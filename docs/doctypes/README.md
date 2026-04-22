# DocType Documentation

This directory contains detailed documentation for each custom DocType created by the CDM app.

## Implemented DocTypes

| DocType | Module | Status | Story |
|---|---|---|---|
| Disease Enrollment | CDM Enrollment | Implemented | 4 |
| Disease Baseline Assessment | CDM Enrollment | Implemented | 6 |
| Baseline Care Gap | CDM Enrollment | Implemented (child table) | 6 |
| Disease Management Settings | CDM Shared | Implemented (single) | 1 |
| CDM Enabled Program | CDM Shared | Implemented (child table) | 1 |
| CDM Allowed Self Entry Type | CDM Shared | Implemented (child table) | 1 |
| CDM Care Plan | CDM Care Plans | Implemented | 7 |
| Care Team Member | CDM Care Plans | Implemented (child table) | 7 |
| Disease Goal | CDM Care Plans | Implemented (linked) | 7 |
| Disease Review Sheet | CDM Reviews | Implemented | 8 |
| Review Side Effect | CDM Reviews | Implemented (child table) | 8 |

## Planned DocTypes

| DocType | Module | Status |
|---|---|---|
| Monitoring Entry | CDM Monitoring | Planned |
| CDM Alert | CDM Monitoring | Planned |
| Protocol Template | CDM Protocols | Planned |
| Protocol Step | CDM Protocols | Planned (child table) |

## Documentation Files

- [disease-enrollment.md](disease-enrollment.md) — Disease Enrollment
- [disease-baseline-assessment.md](disease-baseline-assessment.md) — Disease Baseline Assessment
- [disease-management-settings.md](disease-management-settings.md) — Disease Management Settings
- [cdm-care-plan.md](cdm-care-plan.md) — CDM Care Plan (Story 7)
- [disease-goal.md](disease-goal.md) — Disease Goal (Story 7)
- [disease-review-sheet.md](disease-review-sheet.md) — Disease Review Sheet (Story 8)

## Documentation Template

Each DocType document should cover:
- Purpose and business context
- Fields (with types, options, and validation rules)
- Naming rule
- Workflow / status transitions
- Permissions
- Links to/from other doctypes
- Events and hooks
- API endpoints (if any)
- Test coverage
