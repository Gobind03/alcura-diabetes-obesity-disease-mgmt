"""Programmatic role-permission matrix for all CDM doctypes.

This module defines the permission rules that will be applied to CDM doctype
JSON files when they are created (in future stories). It serves as the single
source of truth for "who can do what" across the app.

Usage by doctype creators::

    from chronic_disease_management.permissions.role_matrix import get_permissions_for_doctype
    permissions = get_permissions_for_doctype("Disease Enrollment")
    # Insert into doctype JSON's "permissions" key
"""

from __future__ import annotations

from chronic_disease_management.constants.roles import (
	ALL_CDM_ROLES,
	CDM_ADMIN,
	CDM_COORDINATOR,
	CDM_DIETITIAN,
	CDM_NURSE,
	CDM_PATIENT,
	CDM_PHYSICIAN,
)

PERMISSION_MATRIX: dict[str, dict[str, dict[str, int]]] = {
	"Disease Enrollment": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Disease Baseline Assessment": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"CDM Care Plan": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1, "write": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Periodic Review": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Home Monitoring Entry": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1, "create": 1},
	},
	"CDM Alert": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1},
		CDM_NURSE: {"read": 1, "write": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Diabetes Profile": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Obesity Profile": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1, "export": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Medication Adherence Log": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1, "create": 1},
	},
	"Medication Side Effect Log": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1, "create": 1},
	},
	"Complication Screening Tracker": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Care Gap": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1},
		CDM_DIETITIAN: {"read": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Diet Plan": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1, "write": 1, "create": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Meal Log": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1, "write": 1, "create": 1},
		CDM_PATIENT: {"read": 1, "create": 1},
	},
	"Activity Log": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1, "write": 1, "create": 1},
		CDM_PATIENT: {"read": 1, "create": 1},
	},
	"Supplement Log": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1, "write": 1, "create": 1},
		CDM_PATIENT: {"read": 1},
	},
	"Care Coordinator Action": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1, "write": 1, "create": 1},
		CDM_NURSE: {"read": 1, "write": 1, "create": 1},
		CDM_COORDINATOR: {"read": 1, "write": 1, "create": 1},
		CDM_DIETITIAN: {"read": 1},
	},
	"Protocol Template": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1},
		CDM_PHYSICIAN: {"read": 1},
		CDM_NURSE: {"read": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
	},
	"Protocol Step": {
		CDM_ADMIN: {"read": 1, "write": 1, "create": 1, "delete": 1},
		CDM_PHYSICIAN: {"read": 1},
		CDM_NURSE: {"read": 1},
		CDM_COORDINATOR: {"read": 1},
		CDM_DIETITIAN: {"read": 1},
	},
	"Disease Management Settings": {
		CDM_ADMIN: {"read": 1, "write": 1},
		CDM_PHYSICIAN: {"read": 1},
		CDM_COORDINATOR: {"read": 1},
	},
}

CDM_DOCTYPES = list(PERMISSION_MATRIX.keys())


def get_permissions_for_doctype(doctype: str) -> list[dict]:
	"""Convert the permission matrix into Frappe's doctype JSON permission format.

	Args:
		doctype: The CDM doctype name.

	Returns:
		A list of permission dicts suitable for the ``permissions`` key in a
		doctype JSON file.

	Raises:
		KeyError: If the doctype is not in the permission matrix.
	"""
	if doctype not in PERMISSION_MATRIX:
		raise KeyError(f"DocType '{doctype}' not found in CDM permission matrix.")

	permissions = []
	for role, perms in PERMISSION_MATRIX[doctype].items():
		entry = {"role": role}
		entry.update(perms)
		permissions.append(entry)
	return permissions


def apply_permissions(doctype: str) -> None:
	"""Programmatically set permissions on a doctype from the matrix.

	This is intended for use during migrations or setup scripts.
	It clears existing custom permissions and replaces them with the matrix values.

	Args:
		doctype: The CDM doctype name.
	"""
	import frappe

	if not frappe.db.exists("DocType", doctype):
		return

	permissions = get_permissions_for_doctype(doctype)
	meta = frappe.get_meta(doctype)

	frappe.db.delete("DocPerm", {"parent": doctype})

	for idx, perm in enumerate(permissions):
		doc = frappe.new_doc("DocPerm")
		doc.parent = doctype
		doc.parenttype = "DocType"
		doc.parentfield = "permissions"
		doc.idx = idx + 1
		doc.role = perm["role"]
		for key in ("read", "write", "create", "delete", "submit", "cancel", "export", "share"):
			doc.set(key, perm.get(key, 0))
		doc.insert(ignore_permissions=True)

	frappe.clear_cache(doctype=doctype)


def validate_permission_matrix() -> dict[str, list[str]]:
	"""Self-test: ensure the permission matrix is internally consistent.

	Returns:
		A dict of issues found. Empty dict means the matrix is valid.
	"""
	issues: dict[str, list[str]] = {}

	all_roles_set = set(ALL_CDM_ROLES)

	for doctype, role_perms in PERMISSION_MATRIX.items():
		for role in role_perms:
			if role not in all_roles_set:
				issues.setdefault(doctype, []).append(
					f"Unknown role '{role}' (not in ALL_CDM_ROLES)"
				)

		for role, perms in role_perms.items():
			if not perms.get("read"):
				issues.setdefault(doctype, []).append(
					f"Role '{role}' has no read permission (unusual)"
				)

	return issues
