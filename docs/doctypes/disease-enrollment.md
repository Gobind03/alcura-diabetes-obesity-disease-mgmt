# Disease Enrollment

## Business Purpose

The Disease Enrollment doctype is the entry point for all chronic disease management workflows. It records a patient's enrollment into a specific disease program (Diabetes, Obesity, Combined Metabolic, or Prediabetes / Metabolic Risk) and tracks the lifecycle of that enrollment from draft through active management to completion or withdrawal.

## DocType Details

| Property | Value |
|---|---|
| Module | CDM Enrollment |
| Naming | `CDM-ENR-.YYYY.-.#####` |
| Track Changes | Yes |
| Title Field | `patient_name` |

## Fields

### Patient Information

| Field | Type | Required | Notes |
|---|---|---|---|
| `patient` | Link -> Patient | Yes | Search-indexed, in list view |
| `patient_name` | Data (Read Only) | - | Fetched from Patient |
| `patient_age` | Data (Read Only) | - | Computed from DOB |
| `patient_sex` | Data (Read Only) | - | Fetched from Patient |

### Program Details

| Field | Type | Required | Notes |
|---|---|---|---|
| `disease_type` | Select | Yes | Diabetes / Obesity / Combined Metabolic / Prediabetes / Metabolic Risk |
| `program_status` | Select | Yes | Draft / Active / On Hold / Completed / Withdrawn. Default: Draft |
| `enrollment_date` | Date | Yes | Default: today. Cannot be in the future |

### Practitioner & Clinic

| Field | Type | Required | Notes |
|---|---|---|---|
| `practitioner` | Link -> Healthcare Practitioner | No | Managing practitioner |
| `practitioner_name` | Data (Read Only) | - | Fetched |
| `primary_clinic` | Link -> Healthcare Service Unit | No | Branch or clinic |
| `company` | Link -> Company | No | Defaults from Disease Management Settings |

### Clinical Context

| Field | Type | Notes |
|---|---|---|
| `source_encounter` | Link -> Patient Encounter | Set when enrollment initiated from OPD |
| `source_appointment` | Link -> Patient Appointment | Set when initiated from appointment |
| `baseline_diagnosis_summary` | Small Text | Free text diagnosis summary |
| `comorbidities_summary` | Small Text | Free text comorbidities |

### Status Tracking

| Field | Type | Notes |
|---|---|---|
| `notes` | Text Editor | Clinical notes |
| `status_change_reason` | Small Text | Reason for last status change |

## Status Lifecycle

```
Draft ──────► Active ──────► On Hold
  │              │               │
  │              ├───► Completed │
  │              │               │
  └───► Withdrawn◄───────────────┘
                 ▲
                 │
           Active ───► Withdrawn
```

### Allowed Transitions

| From | To |
|---|---|
| Draft | Active, Withdrawn |
| Active | On Hold, Completed, Withdrawn |
| On Hold | Active, Withdrawn |
| Completed | (terminal) |
| Withdrawn | (terminal) |

## Validation Rules

1. **Disease type** must be one of the supported types defined in `constants/disease_types.py`.
2. **Enrollment date** cannot be in the future.
3. **Duplicate prevention**: A patient cannot have two active/draft enrollments for the same disease program. The controller checks for existing enrollments on `before_insert`.
4. **Status transitions** are validated against the transition map in `constants/clinical.py`.

## Permissions

| Role | Read | Write | Create | Delete | Export |
|---|---|---|---|---|---|
| CDM Administrator | Yes | Yes | Yes | Yes | Yes |
| CDM Physician | Yes | Yes | Yes | No | Yes |
| CDM Nurse | Yes | Yes | Yes | No | No |
| CDM Coordinator | Yes | Yes | Yes | No | Yes |
| CDM Dietitian | Yes | No | No | No | No |
| CDM Patient | Yes | No | No | No | No |

Portal patients see only their own enrollments via `cdm_permissions.py`.

## API Endpoints

| Method | Endpoint |
|---|---|
| `create_enrollment` | `chronic_disease_management.api.enrollment.create_enrollment` |
| `get_active_enrollment` | `chronic_disease_management.api.enrollment.get_active_enrollment` |
| `update_enrollment_status` | `chronic_disease_management.api.enrollment.update_enrollment_status` |
| `get_enrollment_context` | `chronic_disease_management.api.enrollment.get_enrollment_context` |
| `check_existing_enrollment` | `chronic_disease_management.api.enrollment.check_existing_enrollment` |

## Service Layer

All business logic is in `chronic_disease_management.services.enrollment.EnrollmentService`:

- `create_enrollment()` — validates eligibility, prevents duplicates, creates doc
- `update_status()` — validates transition, saves reason, adds comment
- `close_enrollment()` / `suspend_enrollment()` / `reactivate_enrollment()` / `withdraw_enrollment()` — convenience wrappers
- `get_active_enrollments()` / `get_active_enrollment()` — query methods
- `check_eligibility()` — checks program enabled + duplicate
- `check_existing_enrollment()` — returns non-terminal enrollments for duplicate warnings
- `get_enrollment_context()` — builds pre-fill dict for OPD-triggered enrollment

## Custom Fields on Patient

| Field | Type | Notes |
|---|---|---|
| `cdm_enrolled` | Check (Read Only) | Synced on enrollment update |
| `cdm_active_programs` | Small Text (Read Only) | Comma-separated active programs |

## Example Workflow

1. Clinician opens a Patient record and clicks "Enroll in Disease Program"
2. System checks for existing active enrollments and warns if found
3. Enrollment form opens pre-filled with patient details and practitioner
4. Clinician selects disease program and saves (status: Draft)
5. Clinician activates the enrollment via status button
6. System creates baseline assessment if configured
7. Enrollment remains Active until completed, suspended, or withdrawn
