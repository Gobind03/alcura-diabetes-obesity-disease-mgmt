# ADR-004: Healthcare Adapter Layer

## Status

Accepted

## Date

2026-04-22

## Context

The CDM app needs to read data from multiple Healthcare doctypes (Patient, Patient Encounter, Vital Signs, Lab Test, Medication Request, Patient Appointment, Healthcare Practitioner). These queries could be scattered throughout services, API endpoints, and doctype controllers, creating tight coupling to the Healthcare app's schema.

The Healthcare (Marley Health) app may evolve between versions:
- Fields may be renamed or removed
- Child tables may be restructured
- New doctypes may replace old ones (e.g., `Medication Request` replacing `Drug Prescription`)
- Some installations may have different configurations

We need a strategy that:
1. Centralizes all Healthcare data access
2. Handles schema differences gracefully
3. Makes it easy to adapt when Marley Health upgrades
4. Keeps CDM services testable in isolation

## Decision

We will create a dedicated **adapter layer** (`chronic_disease_management/adapters/`) that:

1. **Encapsulates** all reads from Healthcare doctypes behind stable function signatures.
2. **Guards** against missing doctypes/fields using `require_doctype()` and `optional_doctype()` checks.
3. **Degrades gracefully** — optional features (medication history, appointment history) return empty results if the underlying doctype is unavailable.
4. **Is the sole access path** — CDM services, API endpoints, and doctype controllers must use adapters instead of querying Healthcare doctypes directly.

### Architecture

```
CDM Services --> Adapters --> frappe.db / frappe.get_doc --> Healthcare DocTypes
```

Services never call `frappe.get_all("Patient", ...)` directly. They call `patient_adapter.get_patient_summary(...)` instead.

### Adapter Modules

| Module | Healthcare DocType(s) |
|---|---|
| `base.py` | (framework: compatibility guards, safe wrappers) |
| `patient_adapter.py` | Patient |
| `encounter_adapter.py` | Patient Encounter, Patient Encounter Diagnosis, Drug/Lab/Procedure Prescription |
| `vitals_adapter.py` | Vital Signs |
| `lab_adapter.py` | Lab Test, Lab Test Template |
| `medication_adapter.py` | Medication Request, Drug Prescription |
| `appointment_adapter.py` | Patient Appointment |
| `practitioner_adapter.py` | Healthcare Practitioner |

## Consequences

### Positive

- **Single point of change**: When Marley Health upgrades, only adapters need updating — services remain stable.
- **Testability**: Services can mock adapter functions without needing a live Healthcare installation.
- **Graceful degradation**: Missing optional doctypes don't crash the app.
- **Documentation**: The adapter layer serves as living documentation of which Healthcare fields we depend on.

### Negative

- **Extra layer of indirection**: Developers must route through adapters instead of writing ad-hoc queries.
- **Maintenance cost**: Every new Healthcare field access requires adding to the adapter.

### Mitigations

- Keep adapters thin (mostly `frappe.get_all` / `frappe.db.get_value` wrappers).
- Document the reused doctype mapping comprehensively.
- Run compatibility checks during `after_install` to surface issues early.
