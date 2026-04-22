# ADR-001: Reuse-First Healthcare Architecture

## Status

Accepted

## Date

2026-04-22

## Context

We need to build a Chronic Disease Management module for Diabetes, Obesity, and Combined Metabolic conditions. The target platform already includes Frappe 16, ERPNext 16, HRMS 16, and Marley Health (Healthcare) v16, which collectively provide:

- Patient registration and demographics
- Practitioner management
- Patient Appointments and scheduling
- Patient Encounters (clinical notes)
- Vital Signs recording
- Lab Test ordering and results
- Clinical Procedures
- Medication management
- Patient portal primitives
- Role-based access control

The question is whether to build the CDM module as:

1. **A standalone app** that duplicates patient, encounter, and lab infrastructure
2. **A fork** of Marley Health with CDM features baked in
3. **An extension app** that reuses existing doctypes and adds only domain-specific structures

## Decision

We will build the CDM app as an **extension layer** (option 3) that:

- Reuses existing Healthcare doctypes (Patient, Patient Encounter, Vital Signs, Lab Test, Patient Appointment, Practitioner) as-is, extending them via Custom Fields and doc_events hooks.
- Creates new custom doctypes only for concepts that have no adequate representation in the base platform (Disease Enrollment, CDM Care Plan, Protocol Template, etc.).
- Never forks or directly modifies Frappe, ERPNext, or Marley Health source files.
- Uses Frappe's standard extension mechanisms: hooks, fixtures, Custom Fields, Property Setters, override methods, and server scripts.

## Consequences

### Positive

- **Upgrade safety**: Core apps can be updated independently without merge conflicts.
- **Reduced duplication**: No parallel Patient, Encounter, or Lab Test systems to maintain.
- **Ecosystem compatibility**: Other Frappe apps in the bench continue to work with the same doctypes.
- **Faster development**: We build on top of mature, tested infrastructure.
- **Data integrity**: Single source of truth for patients, encounters, and test results.

### Negative

- **Coupling to upstream schemas**: Changes in Healthcare doctype structure may require adaptation.
- **Limited control**: We cannot change core doctype behavior without hooks or overrides, which may be insufficient for edge cases.
- **Custom Field clutter**: Too many Custom Fields on a single doctype can degrade UX. We must be disciplined about what we add.

### Mitigations

- Pin to major version compatibility (v16) and test against upstream releases.
- Use Custom Fields sparingly; prefer linking to CDM-owned doctypes over adding many fields to Patient.
- Document every integration point so upstream changes can be assessed quickly.
