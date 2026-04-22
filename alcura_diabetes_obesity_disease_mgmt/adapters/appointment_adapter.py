"""Adapter for the Healthcare Patient Appointment doctype."""

from __future__ import annotations

from typing import Any

import frappe

from alcura_diabetes_obesity_disease_mgmt.adapters.base import require_doctype, safe_get_all

_APPOINTMENT_DT = "Patient Appointment"

_APPOINTMENT_FIELDS = [
	"name",
	"patient",
	"patient_name",
	"practitioner",
	"practitioner_name",
	"appointment_date",
	"appointment_time",
	"appointment_type",
	"status",
	"department",
	"duration",
]


def get_upcoming_appointments(
	patient_id: str,
	limit: int = 10,
) -> list[dict]:
	"""Return future appointments for a patient.

	Args:
		patient_id: Patient ID.
		limit: Maximum results.
	"""
	require_doctype(_APPOINTMENT_DT)
	return frappe.get_all(
		_APPOINTMENT_DT,
		filters={
			"patient": patient_id,
			"appointment_date": [">=", frappe.utils.nowdate()],
			"status": ["not in", ["Cancelled"]],
		},
		fields=_APPOINTMENT_FIELDS,
		order_by="appointment_date asc, appointment_time asc",
		limit_page_length=limit,
	)


def get_appointment_history(
	patient_id: str,
	limit: int = 10,
) -> list[dict]:
	"""Return past appointments for a patient.

	Args:
		patient_id: Patient ID.
		limit: Maximum results.
	"""
	return safe_get_all(
		_APPOINTMENT_DT,
		filters={
			"patient": patient_id,
			"appointment_date": ["<", frappe.utils.nowdate()],
		},
		fields=_APPOINTMENT_FIELDS,
		order_by="appointment_date desc, appointment_time desc",
		limit_page_length=limit,
	)
