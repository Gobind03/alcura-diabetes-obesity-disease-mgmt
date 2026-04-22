# Disease Review Sheet

## Purpose

The Disease Review Sheet is a structured clinical review document linked to Patient Encounters. It captures symptom reviews, medication adherence, glycemic events, lifestyle adherence, anthropometric changes, interim events, and clinical assessments during chronic disease follow-up visits.

## Business Context

- Each OPD chronic visit should generate or use a structured review sheet
- The review sheet bridges the Patient Encounter to the CDM enrollment and care plan
- Supports partial saves for multi-step clinical workflows
- Data is structured for future reporting and trend analysis

## Design Decision: Replaces "Periodic Review" (ADR-008)

The codebase previously planned a "Periodic Review" doctype. Story 8 specifies a richer "Disease Review Sheet" that replaces it entirely. All service code, hooks, and references have been updated.

## DocType Details

| Property | Value |
|---|---|
| Module | CDM Reviews |
| Naming | `CDM-RVW-.YYYY.-.#####` |
| Title Field | `patient_name` |
| Track Changes | Yes |

## Review Types

| Type | Use Case |
|---|---|
| New Evaluation | First-time assessment |
| Diabetes Follow-up | Routine diabetes review |
| Obesity Follow-up | Routine obesity review |
| Combined Metabolic Follow-up | Combined metabolic disease review |
| Medication Titration Review | Focused on dose adjustments |
| Lab Review | Lab result follow-up |
| Nutrition Review | Dietary counseling follow-up |

## Clinical Sections

The form is organized in collapsible sections optimized for clinician workflow:

1. **Header** — patient, enrollment, care plan, encounter links, review type
2. **Symptom Review** — symptom summary, new/resolved symptoms
3. **Medication & Adherence** — adherence status, side effects (child table)
4. **Glycemic Events** — hypoglycemia/hyperglycemia episode counts and severity
5. **Nutrition & Lifestyle** — appetite, satiety, diet/activity adherence
6. **Anthropometric Response** — weight response, current weight/BMI, auto-calculated change
7. **Interim Events** — hospitalizations and other events since last review
8. **Clinical Assessment** — impression and plan changes (rich text)
9. **Follow-up** — next review date, action items

## Encounter Integration

- A "Disease Review" button is added to the Patient Encounter form under the CDM group
- Clicking it creates a new review sheet (or navigates to an existing draft) linked to that encounter
- Auto-links active enrollment and care plan based on the patient

## Auto-linking Logic

On validate, the controller:
1. If `enrollment` is empty but `patient` is set, finds the active enrollment
2. If `care_plan` is empty but `enrollment` is set, finds the active care plan
3. Auto-populates `disease_type` from the enrollment

## Weight Change Calculation

On save, if `current_weight` is set, the controller looks up the previous review's weight for the same enrollment and auto-calculates `weight_change_kg`.

## Status Lifecycle

```
Draft → In Progress → Completed
                    → Rescheduled
Scheduled → In Progress → Completed
                        → Rescheduled
          → Missed → Rescheduled
Draft → Cancelled
```

## API Endpoints

- `alcura_diabetes_obesity_disease_mgmt.api.encounter_context.create_review_from_encounter`
- `alcura_diabetes_obesity_disease_mgmt.api.encounter_context.get_enrollment_for_patient`

## Test Coverage

- `tests/test_review_sheet.py` — status transitions, service methods, auto-linking, encounter integration, permissions
- `cdm_reviews/doctype/disease_review_sheet/test_disease_review_sheet.py` — Frappe standard tests
