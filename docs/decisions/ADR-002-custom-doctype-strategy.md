# ADR-002: Custom DocType Strategy

## Status

Accepted

## Date

2026-04-22

## Context

Given the reuse-first architecture (ADR-001), we need clear criteria for when to create a new custom doctype vs. when to extend an existing one with Custom Fields.

## Decision

### Create a Custom DocType when:

1. The concept has its own lifecycle (status transitions, workflow) that does not map to any existing doctype.
2. The concept has multiple fields and child tables that would clutter an existing doctype.
3. The concept needs its own permission model distinct from the host doctype.
4. The concept represents a first-class CDM entity that will appear in reports, dashboards, and portal views independently.

**Examples**: Disease Enrollment, CDM Care Plan, Periodic Review, Monitoring Entry, CDM Alert, Protocol Template.

### Use Custom Fields when:

1. Adding a small number of fields (1-3) to an existing doctype for cross-referencing or flagging.
2. The data logically belongs to the existing doctype and would be confusing if stored elsewhere.
3. The field is used for filtering/reporting on the existing doctype's list view.

**Examples**: `cdm_enrolled` (Check) on Patient, `cdm_review` (Link) on Patient Encounter.

### Use Property Setters when:

1. Changing display properties (hidden, read_only, default) on existing fields.
2. The change is non-destructive and does not alter data storage.

### Use doc_events hooks when:

1. Reacting to lifecycle events (validate, on_submit, on_cancel) on existing doctypes.
2. The logic belongs to the CDM domain, not to the host doctype.

## Consequences

- Custom doctypes are created under CDM-specific modules, keeping the namespace clean.
- Custom Fields are tagged with the CDM module name for clean export/import via fixtures.
- The boundary between "extend" and "create" is documented, reducing ad-hoc decisions.
- New developers can reference this ADR to understand where to place new data structures.
