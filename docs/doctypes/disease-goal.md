# Disease Goal

## Purpose

A Disease Goal represents a single measurable clinical target within a CDM Care Plan. Goals track metrics like HbA1c, weight, BMI, blood pressure, and lifestyle adherence with target values, current measurements, and status tracking.

## Business Context

- Goals are the atomic unit of care plan tracking
- Each goal has its own lifecycle (Not Started → In Progress → Achieved/Partially Met/Not Met)
- Goals support revision-based versioning for audit trails
- Goals are independently queryable for trend reporting and dashboard displays

## Design Decision: Linked DocType (ADR-007)

Goals are implemented as a linked doctype rather than a child table because:
- Individual status lifecycle per goal
- Revision history via self-referential `supersedes` link
- Independent queryability without loading the full care plan
- Better scaling for patients with many goals across multiple plans

## DocType Details

| Property | Value |
|---|---|
| Module | CDM Care Plans |
| Naming | `CDM-GL-.YYYY.-.#####` |
| Title Field | `goal_metric` |
| Track Changes | Yes |

## Key Fields

| Field | Type | Description |
|---|---|---|
| care_plan | Link → CDM Care Plan | Required parent plan |
| patient | Link → Patient | Read-only, fetched from care plan |
| goal_type | Select | Category: Glycemic Control, Weight Management, etc. |
| goal_metric | Select | Specific metric: HbA1c, Fasting Glucose, Weight, BMI, etc. |
| target_value | Data | Single target (e.g., "< 7%") |
| target_range_low | Float | Lower bound for range targets |
| target_range_high | Float | Upper bound for range targets |
| target_unit | Data | Unit of measurement |
| baseline_value | Data | Value at goal creation |
| current_value | Data | Latest measurement |
| rationale | Small Text | Clinical rationale |
| status | Select | Not Started / In Progress / Achieved / Partially Met / Not Met / Revised |
| effective_date | Date | When this goal version becomes effective |
| review_date | Date | When to review progress |
| version | Int | Auto-incremented revision counter |
| supersedes | Link → Disease Goal | Self-referential link to previous version |

## Supported Metrics

| Metric | Default Unit | Typical Goal Type |
|---|---|---|
| HbA1c | % | Glycemic Control |
| Fasting Glucose | mg/dL | Glycemic Control |
| Post-Prandial Glucose | mg/dL | Glycemic Control |
| TIR (Time in Range) | % | Glycemic Control |
| Weight | kg | Weight Management |
| BMI | kg/m² | Weight Management |
| Waist Circumference | cm | Weight Management |
| BP Systolic | mmHg | Blood Pressure |
| BP Diastolic | mmHg | Blood Pressure |
| Activity Minutes/Week | min/week | Exercise |
| Diet Adherence Score | % | Dietary |

## Revision / Versioning Strategy

When a goal needs to be updated (e.g., target tightened after patient progress):

1. The current goal is marked as **Revised** (terminal status)
2. A new Disease Goal is created with:
   - Same `care_plan`, `patient`, `goal_type`, `goal_metric`
   - Updated target value and rationale
   - `baseline_value` set to the old goal's `current_value`
   - `version` incremented
   - `supersedes` pointing to the old goal
3. The revision chain can be traversed via `get_goal_history(goal_id)`

This preserves the full history without complex versioning tables.

## Validation Rules

- At least `target_value` OR both `target_range_low` and `target_range_high` must be set
- If range is used, low must be less than high
- `effective_date` cannot be in the future

## Status Lifecycle

```
Not Started → In Progress → Achieved (terminal)
                          → Partially Met → In Progress (retry)
                                          → Revised (terminal)
                          → Not Met → In Progress (retry)
                                    → Revised (terminal)
                          → Revised (terminal)
```

## Reporting Notes

Goals can be queried across patients for population-level analysis:
- Filter by `goal_metric` and `status` for goal achievement rates
- Filter excluding `status = Revised` for current active goals
- Use `version` and `supersedes` chain for revision analysis
