"""Adapter for the Healthcare Vital Signs doctype.

Provides CDM-relevant vitals access: latest vitals, history, trends, and BMI tracking.
"""

from __future__ import annotations

from typing import Any

import frappe

from chronic_disease_management.adapters.base import (
	require_doctype,
	safe_get_all,
)

_VITALS_DT = "Vital Signs"

_VITALS_FIELDS = [
	"name",
	"patient",
	"signs_date",
	"signs_time",
	"temperature",
	"pulse",
	"respiratory_rate",
	"bp_systolic",
	"bp_diastolic",
	"height",
	"weight",
	"bmi",
	"vital_signs_note",
]


def get_latest_vitals(patient_id: str) -> dict[str, Any] | None:
	"""Return the most recent vital signs record for a patient."""
	require_doctype(_VITALS_DT)
	return frappe.db.get_value(
		_VITALS_DT,
		{"patient": patient_id, "docstatus": 1},
		_VITALS_FIELDS,
		as_dict=True,
		order_by="signs_date desc, signs_time desc",
	)


def get_vitals_history(
	patient_id: str,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
) -> list[dict]:
	"""Return a time series of vital signs records for a patient.

	Args:
		patient_id: Patient ID.
		from_date: Optional start date.
		to_date: Optional end date.
		limit: Maximum records.
	"""
	filters: dict[str, Any] = {"patient": patient_id, "docstatus": 1}
	if from_date and to_date:
		filters["signs_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["signs_date"] = [">=", from_date]
	elif to_date:
		filters["signs_date"] = ["<=", to_date]

	return safe_get_all(
		_VITALS_DT,
		filters=filters,
		fields=_VITALS_FIELDS,
		order_by="signs_date asc, signs_time asc",
		limit_page_length=limit,
	)


def get_vitals_trend(
	patient_id: str,
	vital_field: str,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	"""Return a time series of a single vital parameter (e.g., ``bp_systolic``).

	Args:
		patient_id: Patient ID.
		vital_field: The vital signs field name to trend (e.g., ``bp_systolic``, ``weight``).
		from_date: Optional start date.
		to_date: Optional end date.

	Returns:
		List of dicts with ``signs_date`` and the requested field value.
	"""
	require_doctype(_VITALS_DT)

	filters: dict[str, Any] = {
		"patient": patient_id,
		"docstatus": 1,
		vital_field: ["is", "set"],
	}
	if from_date and to_date:
		filters["signs_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["signs_date"] = [">=", from_date]
	elif to_date:
		filters["signs_date"] = ["<=", to_date]

	return frappe.get_all(
		_VITALS_DT,
		filters=filters,
		fields=["name", "signs_date", vital_field],
		order_by="signs_date asc",
	)


def get_bmi_history(patient_id: str, limit: int = 50) -> list[dict]:
	"""Return weight/height/BMI records over time.

	Only includes records where at least weight or BMI is recorded.
	"""
	require_doctype(_VITALS_DT)

	return frappe.get_all(
		_VITALS_DT,
		filters={
			"patient": patient_id,
			"docstatus": 1,
			"weight": ["is", "set"],
		},
		fields=["name", "signs_date", "height", "weight", "bmi"],
		order_by="signs_date asc",
		limit_page_length=limit,
	)
