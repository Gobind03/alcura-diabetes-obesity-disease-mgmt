# Permissions Matrix

## CDM DocType Permissions by Role

This matrix is implemented programmatically in `alcura_diabetes_obesity_disease_mgmt/permissions/role_matrix.py`. The code is the source of truth; this document is kept in sync.

| DocType | CDM Admin | CDM Physician | CDM Nurse | CDM Coordinator | CDM Dietitian | CDM Patient |
|---|---|---|---|---|---|---|
| Disease Enrollment | CRUDS + Export | CRW + Export | CRW | CRW + Export | R | R (own) |
| CDM Care Plan | CRUDS + Export | CRW + Export | RW | R | RW | R (own) |
| Periodic Review | CRUDS + Export | CRW + Export | CRW | CRW + Export | R | R (own) |
| Monitoring Entry | CRUD + Export | R | R | R | R | CR (own) |
| CDM Alert | CRUD + Export | RW | RW | RW | R | R (own) |
| Protocol Template | CRUD + Export | R | R | R | R | -- |
| Protocol Step | CRUD | R | R | R | R | -- |
| Disease Mgmt Settings | RW | R | -- | R | -- | -- |

### Legend

- **C** = Create
- **R** = Read
- **U/W** = Write/Update
- **D** = Delete
- **S** = Submit/Cancel
- **Export** = Can export data
- **(own)** = Row-level filter to own records via portal and permission_query_conditions
- **--** = No access

## System Manager

System Manager has implicit full access to all doctypes via Frappe's built-in role. It is not listed in the matrix but is always permitted.

## Existing DocType Access

CDM roles do **not** modify permissions on existing Healthcare doctypes. Access to Patient, Patient Encounter, Vital Signs, and Lab Test is governed by existing Healthcare roles. CDM clinician roles should be assigned alongside the appropriate Healthcare roles (e.g., "Physician" + "CDM Physician").

## Portal Permissions

Portal access for CDM Patient role is restricted to:
- Read own Disease Enrollment
- Read own CDM Care Plan and child tables
- Read own Periodic Reviews
- Create and read own Monitoring Entries
- Read own CDM Alerts

All portal queries include a mandatory `patient` filter derived from the logged-in user via `get_cdm_query_conditions()`.

## Row-Level Security

Row-level filtering is implemented via `permission_query_conditions` hooks in `hooks.py`:

```python
permission_query_conditions = {
    "Disease Enrollment": "...cdm_permissions.get_cdm_query_conditions",
    "CDM Care Plan": "...cdm_permissions.get_cdm_query_conditions",
    "Periodic Review": "...cdm_permissions.get_cdm_query_conditions",
    "Monitoring Entry": "...cdm_permissions.get_cdm_query_conditions",
    "CDM Alert": "...cdm_permissions.get_cdm_query_conditions",
}
```

The function returns:
- Empty string for admins and clinicians (unrestricted).
- `patient = '<id>'` for portal patients (own records only).
- `1=0` for users without CDM roles (blocked).

## Validation

Run `validate_permission_matrix()` from `permissions/role_matrix.py` to check internal consistency:
- All roles in the matrix exist in `ALL_CDM_ROLES`.
- All entries have at least read permission.
