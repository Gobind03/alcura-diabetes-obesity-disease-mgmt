# Reused DocType Mapping

## Overview

This document catalogs every Marley Health (Healthcare) doctype that the CDM app depends on, the fields relied upon, and which adapter module provides access.

## Mapping

### Patient

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/patient_adapter.py` |
| CDM Usage | Enrollment target, care plan owner, monitoring subject |
| Required | Yes |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `name` | Data (auto) | Primary key / link target |
| `patient_name` | Data | Display name |
| `first_name`, `last_name` | Data | Name components |
| `sex` | Select | Demographics |
| `dob` | Date | Age calculation |
| `blood_group` | Select | Medical context |
| `status` | Select | Active/Disabled filtering |
| `mobile`, `email` | Data | Contact information |
| `image` | Attach Image | Patient photo |
| `tobacco_past_use`, `tobacco_current_use` | Select | Risk factor assessment |
| `alcohol_past_use`, `alcohol_current_use` | Select | Risk factor assessment |
| `surrounding_factors`, `other_risk_factors` | Small Text | Risk factor detail |
| `allergies` | Table (child) | Allergy list |
| `medical_history`, `surgical_history` | Small Text | Clinical context |
| `user_id` | Link (User) | Portal user resolution |

---

### Patient Encounter

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/encounter_adapter.py` |
| CDM Usage | Periodic reviews link to encounters; prescription/diagnosis data |
| Required | Yes |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `name` | Data (auto) | Primary key / link target |
| `patient` | Link (Patient) | Patient reference |
| `practitioner` | Link (Healthcare Practitioner) | Conducting practitioner |
| `encounter_date`, `encounter_time` | Date/Time | Chronological ordering |
| `medical_department` | Link | Department context |
| `status` | Select | Submission status |
| `appointment` | Link (Patient Appointment) | Appointment linkage |
| `diagnosis` (child table) | Table | Diagnoses from encounter |
| `drug_prescription` (child table) | Table | Medication prescriptions |
| `lab_test_prescription` (child table) | Table | Lab test orders |
| `procedure_prescription` (child table) | Table | Procedure orders |

---

### Vital Signs

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/vitals_adapter.py` |
| CDM Usage | Monitoring entries reference vitals; trend analysis; BMI tracking |
| Required | Yes |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `patient` | Link (Patient) | Patient reference |
| `signs_date`, `signs_time` | Date/Time | Chronological ordering |
| `temperature` | Float | Vital sign |
| `pulse` | Int | Vital sign |
| `respiratory_rate` | Int | Vital sign |
| `bp_systolic`, `bp_diastolic` | Float | Blood pressure monitoring |
| `height`, `weight` | Float | Anthropometric data |
| `bmi` | Float | BMI calculation / tracking |
| `vital_signs_note` | Small Text | Clinical notes |

---

### Lab Test

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/lab_adapter.py` |
| CDM Usage | Monitoring entries reference labs; disease-specific marker tracking |
| Required | Yes |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `patient` | Link (Patient) | Patient reference |
| `template` | Link (Lab Test Template) | Test type identification |
| `lab_test_name` | Data | Display name |
| `result_date` | Date | Chronological ordering |
| `status` | Select | Completion status |
| `practitioner` | Link | Ordering practitioner |
| `lab_test_comment` | Text | Result notes |

---

### Lab Test Template

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/lab_adapter.py` |
| CDM Usage | Protocol steps reference expected tests; marker validation |
| Required | No (optional) |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `name` | Data | Template identification |
| `lab_test_name` | Data | Display name |

---

### Patient Appointment

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/appointment_adapter.py` |
| CDM Usage | Reviews may generate appointments; appointment history |
| Required | No (optional) |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `patient` | Link (Patient) | Patient reference |
| `practitioner` | Link | Appointment practitioner |
| `appointment_date`, `appointment_time` | Date/Time | Scheduling |
| `appointment_type` | Link | Type classification |
| `status` | Select | Appointment status |
| `department` | Link | Department |
| `duration` | Int | Duration in minutes |

---

### Healthcare Practitioner

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/practitioner_adapter.py` |
| CDM Usage | Care plan ownership, review assignment |
| Required | Yes |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `name` | Data (auto) | Primary key / link target |
| `practitioner_name` | Data | Display name |
| `department` | Link | Department affiliation |
| `designation` | Data | Role/specialty |
| `mobile_phone` | Data | Contact |
| `status` | Select | Active/Disabled filtering |

---

### Medication Request

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/medication_adapter.py` |
| CDM Usage | Current medication list, medication snapshot |
| Required | No (optional, graceful degradation) |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `patient` | Link (Patient) | Patient reference |
| `medication` | Link (Medication) | Medication reference |
| `medication_item` | Link (Item) | Item link |
| `status` | Select | Active/completed |
| `order_date` | Date | Ordering date |
| `practitioner`, `practitioner_name` | Link/Data | Prescribing practitioner |

---

### Drug Prescription (Child Table)

| Attribute | Value |
|---|---|
| Source App | Healthcare (Marley Health) |
| Adapter | `adapters/medication_adapter.py` |
| CDM Usage | Encounter-level medication data |
| Required | No (optional, graceful degradation) |

**Fields Used:**

| Field | Type | Used For |
|---|---|---|
| `drug_code` | Link | Drug identification |
| `drug_name` | Data | Display name |
| `dosage` | Data | Dosage details |
| `period` | Data | Duration |
| `dosage_form` | Link | Form (tablet, injection, etc.) |

## Compatibility Notes

1. All adapter methods use `require_doctype()` or `optional_doctype()` guards before querying.
2. If a required doctype is missing, a `CDMDependencyError` is raised with a descriptive message.
3. If an optional doctype is missing, the adapter returns an empty result and logs a warning.
4. Field-level checks are available via `field_exists()` but not applied by default to avoid performance overhead.
5. The adapter layer is the **only** sanctioned path for CDM code to access Healthcare data. Direct `frappe.get_doc("Patient", ...)` calls outside adapters are discouraged.
