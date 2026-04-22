# ADR-005: Disease Enrollment DocType Design

## Status

Accepted

## Context

Story 4 requires a Disease Management Enrollment doctype to act as the entry point for all chronic disease management workflows. Key design decisions include:

- Whether to use Frappe's submittable workflow or a custom status field
- Naming convention
- How to handle duplicate enrollments
- Relationship to existing Healthcare doctypes

## Decision

### Non-Submittable with Custom Status Machine

We chose a non-submittable doctype with a custom `program_status` field and server-enforced state transitions rather than Frappe's built-in submit/cancel workflow. Reasons:

1. **Enrollment has more than two terminal states** (Completed vs Withdrawn) and intermediate states (On Hold) that don't map cleanly to Frappe's docstatus model.
2. **Enrollments are living documents** that clinicians update over time. Submittable docs are immutable after submit, which conflicts with the need to update notes, practitioner, and clinical context.
3. **Status transitions need business rules** (e.g., cannot go from Draft to Completed directly) that are better expressed in a transition map than docstatus.

### Naming Convention: `CDM-ENR-.YYYY.-.#####`

Provides chronological ordering, human-readable prefix, and avoids collisions across years.

### Duplicate Prevention

Active/Draft enrollment uniqueness is enforced per patient + disease_type combination in `before_insert`. The check uses a DB query rather than a unique constraint because:

1. Completed/Withdrawn enrollments for the same patient+program are valid historical records
2. The uniqueness constraint is conditional (only active/draft states)

### Source Linkage

Optional `source_encounter` and `source_appointment` fields preserve the clinical context that triggered enrollment without making it mandatory (direct enrollment from list view is also supported).

## Consequences

- Status transitions must be validated in code (handled by `validators.py` and `clinical.py` transition map)
- UI needs custom buttons for status changes (handled in `disease_enrollment.js`)
- The `program_status` field is the canonical status field; Frappe's `docstatus` remains 0 (Draft) at all times
