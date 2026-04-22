"""Adapter for the Healthcare Patient Encounter doctype.

Provides CDM-relevant encounter data access: latest encounter, history,
diagnoses, and prescriptions linked to an encounter.
"""

from __future__ import annotations

from typing import Any

import frappe

from alcura_diabetes_obesity_disease_mgmt.adapters.base import (
	optional_doctype,
	require_doctype,
	safe_get_all,
)

_ENCOUNTER_DT = "Patient Encounter"

_ENCOUNTER_FIELDS = [
	"name",
	"patient",
	"patient_name",
	"practitioner",
	"practitioner_name",
	"encounter_date",
	"encounter_time",
	"medical_department",
	"status",
	"appointment",
]


def get_latest_encounter(
	patient_id: str,
	practitioner: str | None = None,
) -> dict[str, Any] | None:
	"""Return the most recent encounter for a patient.

	Args:
		patient_id: Patient ID.
		practitioner: Optional filter by practitioner.
	"""
	require_doctype(_ENCOUNTER_DT)

	filters: dict[str, Any] = {"patient": patient_id, "docstatus": 1}
	if practitioner:
		filters["practitioner"] = practitioner

	result = frappe.db.get_value(
		_ENCOUNTER_DT,
		filters,
		_ENCOUNTER_FIELDS,
		as_dict=True,
		order_by="encounter_date desc, encounter_time desc",
	)
	return result


def get_encounter_history(
	patient_id: str,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 10,
) -> list[dict]:
	"""Return paginated encounter history for a patient.

	Args:
		patient_id: Patient ID.
		from_date: Optional start date filter.
		to_date: Optional end date filter.
		limit: Maximum results.
	"""
	filters: dict[str, Any] = {"patient": patient_id, "docstatus": 1}
	if from_date and to_date:
		filters["encounter_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["encounter_date"] = [">=", from_date]
	elif to_date:
		filters["encounter_date"] = ["<=", to_date]

	return safe_get_all(
		_ENCOUNTER_DT,
		filters=filters,
		fields=_ENCOUNTER_FIELDS,
		order_by="encounter_date desc, encounter_time desc",
		limit_page_length=limit,
	)


def get_encounter_diagnoses(encounter_id: str) -> list[dict]:
	"""Return diagnoses from a Patient Encounter's child table.

	Uses the ``Patient Encounter Diagnosis`` child table if available.
	"""
	require_doctype(_ENCOUNTER_DT)
	if not optional_doctype("Patient Encounter Diagnosis"):
		return []

	return frappe.get_all(
		"Patient Encounter Diagnosis",
		filters={"parent": encounter_id, "parenttype": _ENCOUNTER_DT},
		fields=["diagnosis", "description"],
		order_by="idx asc",
	)


def get_encounter_prescriptions(encounter_id: str) -> dict[str, list[dict]]:
	"""Return drug, lab, and procedure prescriptions from an encounter.

	Returns:
		Dict with keys ``drug``, ``lab``, ``procedure`` each containing a list of dicts.
	"""
	require_doctype(_ENCOUNTER_DT)
	result: dict[str, list[dict]] = {"drug": [], "lab": [], "procedure": []}

	if optional_doctype("Drug Prescription"):
		result["drug"] = frappe.get_all(
			"Drug Prescription",
			filters={"parent": encounter_id, "parenttype": _ENCOUNTER_DT},
			fields=["drug_code", "drug_name", "dosage", "period", "dosage_form"],
			order_by="idx asc",
		)

	if optional_doctype("Lab Prescription"):
		result["lab"] = frappe.get_all(
			"Lab Prescription",
			filters={"parent": encounter_id, "parenttype": _ENCOUNTER_DT},
			fields=["lab_test_code", "lab_test_name"],
			order_by="idx asc",
		)

	if optional_doctype("Procedure Prescription"):
		result["procedure"] = frappe.get_all(
			"Procedure Prescription",
			filters={"parent": encounter_id, "parenttype": _ENCOUNTER_DT},
			fields=["procedure", "procedure_name"],
			order_by="idx asc",
		)

	return result
