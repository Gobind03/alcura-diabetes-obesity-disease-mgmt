# CDM Care Plan

## Purpose

The CDM Care Plan is the longitudinal care planning document that sits under a Disease Enrollment. It captures individualized treatment goals, care team assignments, and plan summaries for a patient enrolled in a chronic disease management program.

## Business Context

- Each enrollment should have one active care plan (configurable via settings)
- The care plan is the anchor for all clinical goals and review sheets
- It bridges enrollment → goals → reviews → encounter workflows

## DocType Details

| Property | Value |
|---|---|
| Module | CDM Care Plans |
| Naming | `CDM-CP-.YYYY.-.#####` |
| Title Field | `patient_name` |
| Track Changes | Yes |

## Key Fields

| Field | Type | Description |
|---|---|---|
| enrollment | Link → Disease Enrollment | Required. The parent enrollment |
| patient | Link → Patient | Read-only, fetched from enrollment |
| disease_type | Select | Read-only, fetched from enrollment |
| status | Select | Draft / Active / Under Review / Completed / Cancelled |
| start_date | Date | Required, defaults to today |
| review_date | Date | Next scheduled review |
| practitioner | Link → Healthcare Practitioner | Primary practitioner |
| care_team | Table → Care Team Member | Multi-disciplinary team |
| protocol_template | Link → Protocol Template | Optional template source |
| goals_html | HTML | Auto-rendered summary of linked Disease Goals |
| plan_summary | Text Editor | Free-text plan narrative |
| notes | Text | Additional notes |

## Status Lifecycle

```
Draft → Active → Under Review → Active (re-activate)
                              → Completed
                              → Cancelled
Active → Completed
Active → Cancelled
Draft → Cancelled
```

## Active Plan Strategy

By default, only one active or draft care plan is allowed per enrollment. This is enforced in `before_insert` by querying for existing plans with status Active or Draft.

The constraint can be relaxed by enabling "Allow Multiple Active Care Plans per Enrollment" in Disease Management Settings.

## Goals

Goals are stored as linked `Disease Goal` documents (not child table rows). This design supports:
- Independent status lifecycle per goal
- Revision-based versioning via `supersedes` link
- Independent queryability for dashboards and reports

The `goals_html` field is auto-rendered on every care plan save/update with a summary table of current (non-revised) goals.

## Care Team

The care team is a child table (`Care Team Member`) with:
- Practitioner link
- Role (Lead Physician / Co-managing Physician / Nurse / Coordinator / Dietitian / Other)
- Notes

## Links

| Linked DocType | Via Field | Direction |
|---|---|---|
| Disease Goal | `care_plan` | Goals linked to this plan |
| Disease Review Sheet | `care_plan` | Reviews linked to this plan |
| Disease Enrollment | `enrollment` | Parent enrollment |

## Permissions

| Role | Read | Write | Create | Delete |
|---|---|---|---|---|
| System Manager | Yes | Yes | Yes | Yes |
| CDM Administrator | Yes | Yes | Yes | Yes |
| CDM Physician | Yes | Yes | Yes | No |
| CDM Nurse | Yes | Yes | Yes | No |
| CDM Coordinator | Yes | Yes | Yes | No |
| CDM Dietitian | Yes | No | No | No |
| CDM Patient | Yes | No | No | No |

Portal patients are restricted to their own records via `has_permission` hook.

## API Endpoints

- `chronic_disease_management.api.care_plan.get_active_care_plan`
- `chronic_disease_management.api.care_plan.create_care_plan`
- `chronic_disease_management.api.care_plan.add_goal`
- `chronic_disease_management.api.care_plan.revise_goal`
- `chronic_disease_management.api.care_plan.get_goals`
- `chronic_disease_management.api.care_plan.get_goal_history`

## Test Coverage

- `tests/test_care_plan.py` — status transitions, service methods, controller validation, permission checks
- `cdm_care_plans/doctype/cdm_care_plan/test_cdm_care_plan.py` — Frappe standard tests
