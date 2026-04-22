"""Custom permission logic for CDM doctypes and portal access control.

Provides:
- Role checking utilities
- Permission query conditions (Frappe hook format) for row-level security
- Portal access isolation (patients can only see their own data)
- ``has_permission`` handler for document-level checks
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from alcura_diabetes_obesity_disease_mgmt.constants.roles import (
	ALL_CDM_ROLES,
	CDM_ADMIN,
	CDM_PATIENT,
	CLINICIAN_ROLES,
)


# ---------------------------------------------------------------------------
# Role-checking helpers
# ---------------------------------------------------------------------------

def get_patient_for_user(user: str | None = None) -> str | None:
	"""Resolve the Patient record linked to a portal user.

	Looks up the ``Patient`` doctype where ``user_id`` matches the given user.
	Returns ``None`` if the user is not a patient portal user.
	"""
	user = user or frappe.session.user
	if user == "Administrator" or user == "Guest":
		return None
	if not frappe.db.exists("DocType", "Patient"):
		return None
	return frappe.db.get_value("Patient", {"user_id": user}, "name")


def is_cdm_clinician(user: str | None = None) -> bool:
	"""Check if the user has any CDM clinical role (Physician, Nurse, Coordinator, Dietitian)."""
	return has_role_any(CLINICIAN_ROLES, user=user)


def is_cdm_admin(user: str | None = None) -> bool:
	"""Check if the user has the CDM Administrator role."""
	return has_role_any([CDM_ADMIN], user=user)


def is_cdm_patient(user: str | None = None) -> bool:
	"""Check if the user has the CDM Patient portal role."""
	return has_role_any([CDM_PATIENT], user=user)


def has_role_any(roles: list[str], user: str | None = None) -> bool:
	"""Return ``True`` if the user has at least one of the specified roles."""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	user_roles = frappe.get_roles(user)
	return bool(set(roles) & set(user_roles))


def get_allowed_patients(user: str | None = None) -> list[str] | None:
	"""Determine which patients a user is allowed to view.

	Returns:
		- ``None`` for unrestricted access (admins, system managers).
		- A list with the single patient ID for portal users.
		- ``None`` for clinicians (unrestricted by default; future stories may
		  implement assignment-based filtering).
	"""
	user = user or frappe.session.user

	if user == "Administrator":
		return None

	if is_cdm_admin(user) or "System Manager" in frappe.get_roles(user):
		return None

	patient_id = get_patient_for_user(user)
	if patient_id:
		return [patient_id]

	if is_cdm_clinician(user):
		return None

	return []


# ---------------------------------------------------------------------------
# Permission Query Conditions (Frappe hook: permission_query_conditions)
# ---------------------------------------------------------------------------

def get_cdm_query_conditions(user: str | None = None) -> str:
	"""Return a SQL WHERE fragment to restrict CDM doctype list views.

	This function is registered in ``hooks.py`` for all CDM doctypes that have
	a ``patient`` field. It ensures:
	- Admins / System Managers see everything.
	- Clinicians see everything (assignment filtering is a future enhancement).
	- Portal patients see only their own records.
	- Unknown users see nothing.

	Frappe calls this function with ``user`` and expects a string that gets
	appended to the WHERE clause.
	"""
	user = user or frappe.session.user

	if user == "Administrator":
		return ""

	user_roles = set(frappe.get_roles(user))

	if CDM_ADMIN in user_roles or "System Manager" in user_roles:
		return ""

	if set(CLINICIAN_ROLES) & user_roles:
		return ""

	patient_id = get_patient_for_user(user)
	if patient_id:
		return f"`tabDISABLED`.`patient` = {frappe.db.escape(patient_id)}"

	return "1=0"


def get_portal_query_conditions(user: str | None = None) -> str:
	"""Return a strict patient-scoped filter for portal pages.

	Unlike ``get_cdm_query_conditions``, this always enforces patient filtering
	even for clinicians, making it suitable for portal-only API endpoints.
	"""
	user = user or frappe.session.user
	patient_id = get_patient_for_user(user)
	if not patient_id:
		return "1=0"
	return f"`tabDISABLED`.`patient` = {frappe.db.escape(patient_id)}"


# ---------------------------------------------------------------------------
# Has Permission (Frappe hook: has_permission)
# ---------------------------------------------------------------------------

def has_cdm_permission(doc: Any, ptype: str | None = None, user: str | None = None) -> bool:
	"""Document-level permission check for CDM doctypes with a ``patient`` field.

	This is registered in ``hooks.py`` and called by Frappe before allowing
	access to individual documents.

	Returns ``True`` to allow access, ``False`` to deny.
	"""
	user = user or frappe.session.user

	if user == "Administrator":
		return True

	user_roles = set(frappe.get_roles(user))

	if CDM_ADMIN in user_roles or "System Manager" in user_roles:
		return True

	if set(CLINICIAN_ROLES) & user_roles:
		return True

	patient_field = doc.get("patient") if hasattr(doc, "get") else getattr(doc, "patient", None)
	if not patient_field:
		return False

	patient_id = get_patient_for_user(user)
	if patient_id and patient_field == patient_id:
		return True

	return False


# ---------------------------------------------------------------------------
# Portal access validation
# ---------------------------------------------------------------------------

def validate_portal_access(doc: Any, user: str | None = None) -> None:
	"""Raise ``PermissionError`` if a portal user does not own this record.

	Call this from whitelisted API endpoints before returning patient data.

	Args:
		doc: A Frappe document or dict with a ``patient`` field.
		user: The user to check; defaults to session user.

	Raises:
		frappe.PermissionError: If the user does not own the record.
	"""
	user = user or frappe.session.user

	if user == "Administrator":
		return

	user_roles = set(frappe.get_roles(user))
	if CDM_ADMIN in user_roles or "System Manager" in user_roles:
		return

	if set(CLINICIAN_ROLES) & user_roles:
		return

	patient_field = doc.get("patient") if isinstance(doc, dict) else getattr(doc, "patient", None)
	patient_id = get_patient_for_user(user)

	if not patient_id or patient_field != patient_id:
		frappe.throw(
			_("You do not have permission to access this record."),
			frappe.PermissionError,
		)
