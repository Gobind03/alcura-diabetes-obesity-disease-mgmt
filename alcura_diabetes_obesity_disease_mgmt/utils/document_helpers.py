"""Safe document creation/retrieval helpers and CDM settings accessor."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def safe_get_doc(
	doctype: str,
	name: str,
	raise_on_missing: bool = False,
) -> Any | None:
	"""Fetch a document, returning ``None`` instead of raising if it does not exist.

	Args:
		doctype: The DocType name.
		name: The document name/ID.
		raise_on_missing: If ``True``, raise ``frappe.DoesNotExistError`` when not found.
	"""
	if not frappe.db.exists(doctype, name):
		if raise_on_missing:
			frappe.throw(
				_("{0} {1} does not exist.").format(doctype, name),
				frappe.DoesNotExistError,
			)
		return None
	return frappe.get_doc(doctype, name)


def safe_create_doc(
	doctype: str,
	values: dict,
	ignore_permissions: bool = False,
	deduplicate_field: str | None = None,
) -> Any:
	"""Create a document idempotently.

	If *deduplicate_field* is given and a record with a matching value already
	exists, the existing document is returned instead of creating a duplicate.

	Args:
		doctype: The DocType name.
		values: Field values for the new document.
		ignore_permissions: Bypass permission checks.
		deduplicate_field: Optional field name used to check for existing records.

	Returns:
		The newly created (or existing) Frappe document.
	"""
	if deduplicate_field and deduplicate_field in values:
		existing = frappe.db.exists(doctype, {deduplicate_field: values[deduplicate_field]})
		if existing:
			return frappe.get_doc(doctype, existing)

	doc = frappe.new_doc(doctype)
	doc.update(values)
	doc.flags.ignore_permissions = ignore_permissions
	doc.insert()
	return doc


def get_cdm_settings():
	"""Return the cached Disease Management Settings singleton.

	Uses Frappe's document cache so repeated calls within a request are free.
	"""
	return frappe.get_cached_doc("Disease Management Settings")


def get_enabled_programs() -> list[str]:
	"""Return the list of currently enabled disease program type strings."""
	settings = get_cdm_settings()
	return settings.get_enabled_program_list()


def patient_lookup(patient_id: str) -> dict | None:
	"""Return a lightweight summary dict for a patient, or ``None`` if not found.

	Keys: ``name``, ``patient_name``, ``sex``, ``dob``, ``status``.
	"""
	if not frappe.db.exists("Patient", patient_id):
		return None
	return frappe.db.get_value(
		"Patient",
		patient_id,
		["name", "patient_name", "sex", "dob", "status"],
		as_dict=True,
	)


def program_lookup(patient_id: str, disease_type: str) -> dict | None:
	"""Check whether a patient has an active enrollment for *disease_type*.

	Returns the enrollment dict or ``None``.
	"""
	if not frappe.db.exists("DocType", "Disease Enrollment"):
		return None

	enrollment = frappe.db.get_value(
		"Disease Enrollment",
		{"patient": patient_id, "disease_type": disease_type, "status": "Active"},
		["name", "disease_type", "status", "enrollment_date"],
		as_dict=True,
	)
	return enrollment
