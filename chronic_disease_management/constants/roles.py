"""CDM-specific role names.

These roles are created during app installation and used for permission checks.
They are additive to existing Healthcare / ERPNext roles.
System Manager is not listed here — Frappe grants full access to that role natively.
"""

CDM_COORDINATOR = "CDM Coordinator"
CDM_PHYSICIAN = "CDM Physician"
CDM_NURSE = "CDM Nurse"
CDM_DIETITIAN = "CDM Dietitian"
CDM_PATIENT = "CDM Patient"
CDM_ADMIN = "CDM Administrator"

ALL_CDM_ROLES: list[str] = [
	CDM_COORDINATOR,
	CDM_PHYSICIAN,
	CDM_NURSE,
	CDM_DIETITIAN,
	CDM_PATIENT,
	CDM_ADMIN,
]

CLINICIAN_ROLES: list[str] = [
	CDM_COORDINATOR,
	CDM_PHYSICIAN,
	CDM_NURSE,
	CDM_DIETITIAN,
]

DESK_ROLES: list[str] = [
	CDM_COORDINATOR,
	CDM_PHYSICIAN,
	CDM_NURSE,
	CDM_DIETITIAN,
	CDM_ADMIN,
]

PORTAL_ROLES: list[str] = [
	CDM_PATIENT,
]
