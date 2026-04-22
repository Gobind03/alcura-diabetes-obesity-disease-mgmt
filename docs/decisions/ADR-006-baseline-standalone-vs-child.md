# ADR-006: Baseline Assessment as Standalone DocType with Snapshot Approach

## Status

Accepted

## Context

Story 6 requires a structured baseline profile linked to enrollment. Two design options were considered:

1. **Child table** embedded within Disease Enrollment
2. **Standalone doctype** linked 1:1 to Disease Enrollment

Additionally, the data storage strategy could be:

A. **Live links** -- store only references to Vital Signs / Lab Test records
B. **Snapshot** -- copy values into the baseline at a point in time, with source traceability

## Decision

### Standalone DocType (Option 2)

The baseline is a standalone doctype (`Disease Baseline Assessment`) with a unique Link back to `Disease Enrollment`. Reasons:

1. **Complexity** -- The baseline has 30+ fields across 8 sections (diagnosis, anthropometrics, vitals, labs, medications, complications, risk markers, lifestyle). This would bloat the enrollment form as a child table.
2. **Independent lifecycle** -- Baselines can be created, refreshed, and reviewed independently of enrollment status changes.
3. **Permissions** -- Different roles may need different access to baseline data vs enrollment data.
4. **Separate form** -- Clinicians benefit from a dedicated form focused on clinical assessment.

### Snapshot Approach (Option B)

Values are copied from Healthcare records into the baseline at creation time, with source links preserved for audit. Reasons:

1. **Point-in-time accuracy** -- The baseline should not change when new vitals are recorded later.
2. **Clinician curation** -- Doctors may annotate or correct auto-fetched values. Live links would overwrite.
3. **Offline resilience** -- The baseline works even if source records are amended or deleted.
4. **Refresh on demand** -- The `refresh_baseline` API allows clinicians to explicitly re-pull data when they choose, with control over overwriting.

The split between auto-fetchable fields and clinician-curated fields is tracked in the controller's `_AUTO_FETCHABLE_FIELDS` set.

## Consequences

- A 1:1 constraint between enrollment and baseline must be enforced in code (done via `unique=1` on the enrollment Link field and a `before_validate` check)
- The snapshot may become stale; the "Refresh" button and `last_refreshed` field mitigate this
- Care gaps are computed from the snapshot, not from live data
- Future stories may add a "Baseline History" by allowing re-assessment (amend-and-resubmit pattern)
