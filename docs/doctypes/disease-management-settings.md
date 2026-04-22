# Disease Management Settings

## Overview

**Disease Management Settings** is a Single doctype that holds the global configuration for the CDM app. It controls which disease programs are active, review scheduling intervals, alert thresholds, protocol engine behavior, and patient portal features.

Access it in the Frappe UI via **CDM Shared > Disease Management Settings**.

## Module

CDM Shared

## Fields

### General

| Field | Type | Description | Default |
|---|---|---|---|
| `enabled_programs` | Table (CDM Enabled Program) | Which disease programs are active | All three on install |
| `default_company` | Link (Company) | Default company for CDM operations | -- |

### Review Configuration

| Field | Type | Description | Default |
|---|---|---|---|
| `diabetes_review_interval_days` | Int | Days between diabetes reviews | 90 |
| `obesity_review_interval_days` | Int | Days between obesity reviews | 60 |
| `metabolic_review_interval_days` | Int | Days between metabolic reviews | 90 |
| `missed_review_grace_days` | Int | Grace days before a missed review triggers alerts | 7 |

### Alert Thresholds

| Field | Type | Description | Default |
|---|---|---|---|
| `hba1c_critical_threshold` | Float | HbA1c % for critical alert | 9.0 |
| `hba1c_warning_threshold` | Float | HbA1c % for warning alert | 7.5 |
| `bmi_critical_threshold` | Float | BMI for critical alert | 40.0 |
| `bmi_warning_threshold` | Float | BMI for warning alert | 35.0 |
| `bp_systolic_critical` | Int | Systolic BP (mmHg) for critical alert | 180 |
| `bp_systolic_warning` | Int | Systolic BP (mmHg) for warning alert | 140 |
| `fbs_critical_high` | Float | Fasting blood sugar (mg/dL) for critical alert | 300 |
| `fbs_warning_high` | Float | Fasting blood sugar (mg/dL) for warning alert | 200 |

### Protocol Engine

| Field | Type | Description | Default |
|---|---|---|---|
| `enable_protocol_engine` | Check | Master toggle for protocol-based care plan generation | 1 (enabled) |
| `auto_create_care_plan_on_enrollment` | Check | Auto-create care plan when patient is enrolled | 1 |
| `auto_schedule_reviews` | Check | Auto-schedule periodic reviews based on intervals | 1 |

### Patient Portal

| Field | Type | Description | Default |
|---|---|---|---|
| `enable_patient_portal` | Check | Enable CDM patient portal features | 1 |
| `allow_self_monitoring_entry` | Check | Allow patients to submit monitoring data | 1 |
| `allowed_self_entry_types` | Table (CDM Allowed Self Entry Type) | Which entry types patients can submit | Blood Glucose, Blood Pressure, Weight |
| `show_care_plan_to_patient` | Check | Show care plan details in portal | 1 |
| `show_lab_results_to_patient` | Check | Show lab results in portal | 1 |

## Validation Rules

1. At least one disease program must be enabled.
2. No duplicate programs in the enabled list.
3. Warning thresholds must be strictly less than critical thresholds (HbA1c, BMI, BP, FBS).
4. Review intervals must be at least 1 day.

## Permissions

| Role | Access |
|---|---|
| System Manager | Full CRUD |
| CDM Administrator | Read + Write |
| CDM Physician | Read only |
| CDM Coordinator | Read only |

## Programmatic Access

```python
from alcura_diabetes_obesity_disease_mgmt.utils.document_helpers import get_cdm_settings

settings = get_cdm_settings()  # cached singleton
interval = settings.get_review_interval("Diabetes")  # 90
enabled = settings.is_program_enabled("Obesity")  # True/False
programs = settings.get_enabled_program_list()  # ["Diabetes", "Obesity", ...]
entry_types = settings.get_allowed_self_entry_types()  # ["Blood Glucose", ...]
```

## Installation

The singleton is auto-created during `after_install` with sensible defaults. See `alcura_diabetes_obesity_disease_mgmt/setup/install.py`.

## Child Tables

### CDM Enabled Program

| Field | Type | Options |
|---|---|---|
| `disease_type` | Select | Diabetes, Obesity, Combined Metabolic |

### CDM Allowed Self Entry Type

| Field | Type | Options |
|---|---|---|
| `entry_type` | Select | Blood Glucose, Blood Pressure, Weight, Dietary Log, Exercise Log, Medication Taken, Symptom Report |
