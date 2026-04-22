# Disease Baseline Assessment

## Business Purpose

The Disease Baseline Assessment captures a structured, point-in-time clinical profile when a patient is enrolled into a chronic disease management program. It serves as the foundation for goal-setting, care planning, and longitudinal tracking by establishing where the patient stands at enrollment.

## Design Rationale: Snapshot vs Live Link

This doctype uses a **snapshot** approach rather than live links to Vital Signs / Lab Test records. Reasons:

1. **Point-in-time reference** -- The baseline should reflect the patient's state at enrollment, not change when new vitals are recorded.
2. **Clinician curation** -- Clinicians may adjust or annotate baseline values (e.g., correcting a lab value, adding context). Live links would overwrite these.
3. **Performance** -- A single document with denormalized fields is faster to load and display than joining across multiple doctypes.
4. **Source traceability** -- The `vitals_source`, `vitals_date`, and `labs_source_date` fields maintain links back to source records for audit.

The `Refresh from Healthcare Data` button allows clinicians to re-pull data on demand, with control over whether to overwrite manual entries.

## DocType Details

| Property | Value |
|---|---|
| Module | CDM Enrollment |
| Naming | `CDM-BLA-.YYYY.-.#####` |
| Track Changes | Yes |
| Title Field | `patient_name` |
| 1:1 Constraint | One baseline per enrollment (enforced in controller + unique on `enrollment`) |

## Fields

### Enrollment & Patient

| Field | Type | Notes |
|---|---|---|
| `enrollment` | Link -> Disease Enrollment | Required, unique |
| `patient` | Link -> Patient | Fetched from enrollment, read-only |
| `patient_name` | Data | Read-only |
| `disease_type` | Data | Read-only, fetched from enrollment |
| `source_encounter` | Link -> Patient Encounter | Optional |
| `assessment_date` | Date | Default: today |

### Diagnosis

| Field | Type | Notes |
|---|---|---|
| `diagnosis_type` | Select | Type 1 DM / Type 2 DM / GDM / Obesity Class I-III / Prediabetes / Metabolic Syndrome / Other |
| `diagnosis_duration_months` | Int | Duration since diagnosis |
| `diagnosis_notes` | Small Text | |

### Anthropometrics

| Field | Type | Notes |
|---|---|---|
| `height_cm` | Float | Auto-fetched from Vital Signs |
| `weight_kg` | Float | Auto-fetched from Vital Signs |
| `bmi` | Float (Read Only) | Auto-calculated: weight / (height/100)^2 |
| `waist_circumference_cm` | Float | Manual entry |
| `obesity_class` | Select (Read Only) | Auto-derived from BMI using WHO classification |

### Vitals Snapshot

| Field | Type | Notes |
|---|---|---|
| `bp_systolic` / `bp_diastolic` / `pulse` | Int | Auto-fetched |
| `vitals_source` | Link -> Vital Signs | Source record (read-only) |
| `vitals_date` | Date | Date of source vitals (read-only) |

### Key Lab Results Snapshot

All Float fields for: HbA1c, FBS, PPBS, Total Cholesterol, LDL, HDL, Triglycerides, Serum Creatinine, eGFR, Urine Microalbumin.

`labs_source_date` tracks the most recent lab date used.

### Medications, Complications, Risk Markers, Lifestyle Readiness

See doctype JSON for full field list. These are clinician-curated sections not auto-fetched.

### Care Gaps (Child Table: Baseline Care Gap)

| Field | Type |
|---|---|
| `gap_type` | Select: Vital Signs / Lab Test / Medication Review / Screening / Other |
| `description` | Data |
| `status` | Select: Open / In Progress / Closed / Deferred / Not Applicable |
| `priority` | Select: High / Medium / Low |
| `notes` | Small Text |

### Data Quality

| Field | Notes |
|---|---|
| `data_completeness_pct` | Auto-computed from 23 clinical fields |
| `last_refreshed` | Datetime of last auto-fetch |
| `refresh_notes` | Summary of auto-fetched vs manual |

## Auto-Prefill Strategy

When a baseline is created, `BaselineService.prefill_from_healthcare_data` executes:

1. **Vitals**: `vitals_adapter.get_latest_vitals(patient)` -> populates height, weight, BP, pulse
2. **Labs**: `lab_adapter.get_latest_lab_result(patient, template)` -> checks for HbA1c, FBS, etc.
3. **Medications**: `medication_adapter.get_medication_snapshot(patient)` -> formatted text snapshot

After prefill, `identify_care_gaps` checks disease-type-specific expected fields and creates child rows for any missing items.

## Refresh Behavior

The `refresh_baseline` method re-runs prefill with an option:

- **Default** (`overwrite_manual=False`): Only updates auto-fetchable fields; preserves clinician-curated content
- **Force** (`overwrite_manual=True`): Overwrites all fields

Auto-fetchable fields are defined in `_AUTO_FETCHABLE_FIELDS` in the controller.

## Permissions

| Role | Read | Write | Create | Delete |
|---|---|---|---|---|
| CDM Administrator | Yes | Yes | Yes | Yes |
| CDM Physician | Yes | Yes | Yes | No |
| CDM Nurse | Yes | Yes | Yes | No |
| CDM Coordinator | Yes | No | No | No |
| CDM Dietitian | Yes | No | No | No |
| CDM Patient | Yes | No | No | No |

## API Endpoints

| Method | Endpoint |
|---|---|
| `create_baseline_assessment` | `alcura_diabetes_obesity_disease_mgmt.api.enrollment.create_baseline_assessment` |
| `refresh_baseline` | `alcura_diabetes_obesity_disease_mgmt.api.enrollment.refresh_baseline` |
