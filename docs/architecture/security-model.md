# Security Model

## Principles

1. **Least privilege**: Each role gets only the permissions necessary for its function.
2. **Patient isolation**: Portal users can only see their own data. No patient-to-patient leakage.
3. **Audit trail**: Critical changes to enrollments, care plans, goals, and alerts are logged.
4. **Defense in depth**: Server-side permission checks enforce access control regardless of client behavior.

## Role Hierarchy

| Role | Desk Access | Portal Access | Scope |
|---|---|---|---|
| CDM Administrator | Yes | No | Full CRUD on all CDM doctypes; role/config management |
| CDM Physician | Yes | No | Read/write on enrollments, care plans, reviews for assigned patients |
| CDM Nurse | Yes | No | Read/write on enrollments, reviews; read on care plans and monitoring |
| CDM Coordinator | Yes | No | Manage enrollments, schedule reviews, view dashboards |
| CDM Dietitian | Yes | No | Read/write on care plan dietary goals and interventions |
| CDM Patient | No | Yes | Read own enrollment, care plan, monitoring; submit self-monitoring data |

System Manager has implicit full access via Frappe's built-in role.

## Permission Enforcement

### DocType Permissions

Standard Frappe role-based permissions are defined in the permission matrix (`alcura_diabetes_obesity_disease_mgmt/permissions/role_matrix.py`). The matrix covers all CDM doctypes and is the single source of truth. See [permissions-matrix.md](permissions-matrix.md) for the full table.

### Permission Query Conditions

For all CDM doctypes with a `patient` field, custom `permission_query_conditions` are registered in `hooks.py`. The function `get_cdm_query_conditions()` in `permissions/cdm_permissions.py`:

- Returns an empty string (no filter) for Administrators, CDM Admins, System Managers, and clinicians.
- Returns a `patient = '<patient_id>'` filter for portal users.
- Returns `1=0` (block all) for users without any CDM role.

### Document-Level Permission (has_permission)

The function `has_cdm_permission()` is registered for the same CDM doctypes. It performs document-level checks:

- Administrator / CDM Admin / System Manager: always allowed.
- Clinicians: always allowed (assignment-based filtering is a future enhancement).
- Portal patients: allowed only if `doc.patient` matches their linked Patient record.
- Others: denied.

### Portal Access Control

- Portal pages use `frappe.has_permission()` checks before rendering.
- Whitelisted API endpoints call `validate_portal_access(doc)` which raises `frappe.PermissionError` if the logged-in user does not own the record.
- All portal API methods use `@frappe.whitelist(allow_guest=False)`.
- The `get_portal_query_conditions()` function enforces strict patient filtering even for non-portal contexts, suitable for portal-only endpoints.

See [portal-access-model.md](portal-access-model.md) for detailed portal isolation documentation.

### Utility Functions

The `permissions/cdm_permissions.py` module provides reusable helpers:

| Function | Purpose |
|---|---|
| `get_patient_for_user(user)` | Resolve Patient record from portal user |
| `is_cdm_clinician(user)` | Check if user has any clinical role |
| `is_cdm_admin(user)` | Check if user has CDM Administrator role |
| `is_cdm_patient(user)` | Check if user has CDM Patient role |
| `has_role_any(roles, user)` | Check if user has at least one of the given roles |
| `get_allowed_patients(user)` | Get list of patient IDs a user can access |
| `validate_portal_access(doc, user)` | Raise PermissionError if portal user doesn't own the record |

## Audit Logging

The `permissions/audit.py` module provides:

- `log_status_change(doctype, name, field, old_value, new_value)` — creates a Comment on the document timeline for status transitions.
- `log_critical_action(action_type, details, reference_doctype, reference_name)` — logs protocol overrides, alert dismissals, and other significant actions.
- `get_audit_trail(doctype, name)` — retrieves CDM-specific audit comments for a document.

These complement Frappe's built-in Version tracking (field-level change history on submitted documents).

## Data Protection

- Patient health data in reports and dashboards is filtered by the user's role and assigned patient set.
- Exports (CSV, PDF) respect the same permission model via query conditions.
- Sensitive fields are excluded from global search indexing where appropriate.
- The Disease Management Settings doctype has `track_changes = 1` enabled for configuration audit.
