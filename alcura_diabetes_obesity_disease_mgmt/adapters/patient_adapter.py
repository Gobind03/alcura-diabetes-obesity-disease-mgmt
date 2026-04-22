"""Adapter for the Healthcare Patient doctype.

Provides CDM-relevant patient data access without scattering direct
``frappe.get_doc("Patient", ...)`` calls across the codebase.
"""

from __future__ import annotations

from typing import Any

import frappe

from alcura_diabetes_obesity_disease_mgmt.adapters.base import (
	require_doctype,
	safe_get_all,
	safe_get_value,
)

_PATIENT_DT = "Patient"

_SUMMARY_FIELDS = [
	"name",
	"patient_name",
	"first_name",
	"last_name",
	"sex",
	"dob",
	"blood_group",
	"status",
	"mobile",
	"email",
	"image",
]

_RISK_FACTOR_FIELDS = [
	"tobacco_past_use",
	"tobacco_current_use",
	"alcohol_past_use",
	"alcohol_current_use",
	"surrounding_factors",
	"other_risk_factors",
]


def get_patient_summary(patient_id: str) -> dict[str, Any]:
	"""Return demographics and status for a patient.

	Raises:
		CDMDependencyError: If the Patient doctype is missing.
	"""
	require_doctype(_PATIENT_DT)
	data = frappe.db.get_value(
		_PATIENT_DT,
		patient_id,
		_SUMMARY_FIELDS,
		as_dict=True,
	)
	if not data:
		frappe.throw(f"Patient '{patient_id}' not found.", frappe.DoesNotExistError)
	return data


def get_patient_risk_factors(patient_id: str) -> dict[str, Any]:
	"""Return risk factor fields for a patient."""
	require_doctype(_PATIENT_DT)
	data = frappe.db.get_value(
		_PATIENT_DT,
		patient_id,
		_RISK_FACTOR_FIELDS,
		as_dict=True,
	)
	return data or {}


def get_patient_allergies(patient_id: str) -> list[dict]:
	"""Return allergy child table entries for a patient."""
	require_doctype(_PATIENT_DT)
	if not frappe.db.exists(_PATIENT_DT, patient_id):
		return []
	doc = frappe.get_doc(_PATIENT_DT, patient_id)
	return [row.as_dict() for row in (doc.get("allergies") or [])]


def get_patient_medical_history(patient_id: str) -> dict[str, Any]:
	"""Return medical and surgical history fields."""
	require_doctype(_PATIENT_DT)
	data = frappe.db.get_value(
		_PATIENT_DT,
		patient_id,
		["medical_history", "surgical_history", "patient_details"],
		as_dict=True,
	)
	return data or {}


def search_patients(
	filters: dict | None = None,
	search_term: str | None = None,
	limit: int = 20,
) -> list[dict]:
	"""Search patients with optional CDM-relevant filters.

	Args:
		filters: Standard Frappe filter dict.
		search_term: Free-text search against ``patient_name``.
		limit: Max results.
	"""
	effective_filters: dict[str, Any] = dict(filters or {})
	if search_term:
		effective_filters["patient_name"] = ["like", f"%{search_term}%"]

	return safe_get_all(
		_PATIENT_DT,
		filters=effective_filters,
		fields=["name", "patient_name", "sex", "dob", "status", "mobile"],
		order_by="patient_name asc",
		limit_page_length=limit,
	)
