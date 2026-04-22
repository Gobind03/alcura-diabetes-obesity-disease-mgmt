# ADR-003: Portal Security Boundaries

## Status

Accepted

## Date

2026-04-22

## Context

The CDM app includes a patient-facing portal where patients can:

- View their disease enrollment status
- View their care plan and goals
- Submit self-monitoring data (weight, blood glucose, etc.)
- View upcoming and past reviews
- View alerts

Patient health data is sensitive. We must prevent:

- Patient A seeing Patient B's data
- Unauthorized data modification
- Data leakage through portal APIs
- Elevation of privilege from portal to desk

## Decision

### 1. Patient Identity Binding

Every portal request resolves the logged-in user to their Patient record using `frappe.db.get_value("Patient", {"user": frappe.session.user})`. All queries include this patient as a mandatory filter.

### 2. Whitelisted API Only

Portal pages interact with the server exclusively through `@frappe.whitelist(allow_guest=False)` endpoints defined in `alcura_diabetes_obesity_disease_mgmt.api.portal`. No direct DocType REST API access is exposed to portal users.

### 3. Server-Side Filtering

Even if a portal user crafts a request with a different patient's name, the API endpoint re-derives the patient from `frappe.session.user` and ignores the client-supplied value.

### 4. CDM Patient Role

The `CDM Patient` role has:
- `desk_access = 0` (no desk access)
- Read-only access to own CDM records only
- Write access only to Monitoring Entry (for self-reported data)

### 5. No Global Search Exposure

CDM doctypes containing health data are excluded from global search to prevent accidental information disclosure.

### 6. Audit Trail

All patient-submitted data (Monitoring Entries) is timestamped and linked to the submitting user. Modifications by clinicians are tracked via Frappe's Version system.

## Consequences

### Positive

- Strong isolation between patients.
- No reliance on client-side security.
- Audit trail for regulatory compliance.

### Negative

- Portal development requires writing explicit API endpoints rather than using Frappe's generic APIs.
- Every new portal feature needs a corresponding permission test.

### Mitigations

- Standardize a `get_current_patient()` utility in `alcura_diabetes_obesity_disease_mgmt.utils.validators` that all portal APIs call.
- Create a `test_portal_isolation` test helper that verifies patient A cannot access patient B's records for any given doctype.
