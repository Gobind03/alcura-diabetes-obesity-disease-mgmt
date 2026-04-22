"""Adapter for Healthcare medication-related doctypes.

Abstracts over both the ``Medication Request`` standalone doctype and the
``Drug Prescription`` child table embedded in Patient Encounters.
"""

from __future__ import annotations

from typing import Any

import frappe

from chronic_disease_management.adapters.base import (
	optional_doctype,
	safe_get_all,
)

_MEDICATION_REQUEST_DT = "Medication Request"
_DRUG_PRESCRIPTION_DT = "Drug Prescription"
_ENCOUNTER_DT = "Patient Encounter"


def get_current_medications(patient_id: str) -> list[dict]:
	"""Return active medication requests for a patient.

	Falls back to an empty list if ``Medication Request`` is not installed.
	"""
	if not optional_doctype(_MEDICATION_REQUEST_DT):
		return []

	return safe_get_all(
		_MEDICATION_REQUEST_DT,
		filters={
			"patient": patient_id,
			"status": ["in", ["Active", "active", "Draft"]],
			"docstatus": ["<", 2],
		},
		fields=[
			"name",
			"medication",
			"medication_item",
			"status",
			"order_date",
			"practitioner",
			"practitioner_name",
		],
		order_by="order_date desc",
	)


def get_medication_snapshot(
	patient_id: str,
	as_of_date: str | None = None,
) -> list[dict]:
	"""Return a point-in-time medication list for a patient.

	Combines ``Medication Request`` data (if available) with encounter-level
	``Drug Prescription`` entries for a comprehensive view.

	Args:
		patient_id: Patient ID.
		as_of_date: Optional cutoff date; defaults to all records.
	"""
	medications: list[dict] = []

	if optional_doctype(_MEDICATION_REQUEST_DT):
		filters: dict[str, Any] = {"patient": patient_id, "docstatus": ["<", 2]}
		if as_of_date:
			filters["order_date"] = ["<=", as_of_date]
		medications.extend(
			safe_get_all(
				_MEDICATION_REQUEST_DT,
				filters=filters,
				fields=[
					"name",
					"medication",
					"medication_item",
					"status",
					"order_date",
					"practitioner_name",
				],
				order_by="order_date desc",
			)
		)

	if optional_doctype(_DRUG_PRESCRIPTION_DT) and optional_doctype(_ENCOUNTER_DT):
		encounter_filters: dict[str, Any] = {"patient": patient_id, "docstatus": 1}
		if as_of_date:
			encounter_filters["encounter_date"] = ["<=", as_of_date]
		encounters = frappe.get_all(
			_ENCOUNTER_DT,
			filters=encounter_filters,
			fields=["name"],
			order_by="encounter_date desc",
			limit_page_length=10,
		)
		for enc in encounters:
			prescriptions = frappe.get_all(
				_DRUG_PRESCRIPTION_DT,
				filters={"parent": enc.name, "parenttype": _ENCOUNTER_DT},
				fields=["drug_code", "drug_name", "dosage", "period", "dosage_form"],
				order_by="idx asc",
			)
			for rx in prescriptions:
				rx["source"] = "Encounter"
				rx["encounter"] = enc.name
			medications.extend(prescriptions)

	return medications


def get_medication_history(
	patient_id: str,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
) -> list[dict]:
	"""Return historical medication requests for a patient.

	Args:
		patient_id: Patient ID.
		from_date: Optional start date.
		to_date: Optional end date.
		limit: Maximum results.
	"""
	if not optional_doctype(_MEDICATION_REQUEST_DT):
		return []

	filters: dict[str, Any] = {"patient": patient_id}
	if from_date and to_date:
		filters["order_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["order_date"] = [">=", from_date]
	elif to_date:
		filters["order_date"] = ["<=", to_date]

	return safe_get_all(
		_MEDICATION_REQUEST_DT,
		filters=filters,
		fields=[
			"name",
			"medication",
			"medication_item",
			"status",
			"order_date",
			"practitioner_name",
		],
		order_by="order_date desc",
		limit_page_length=limit,
	)
