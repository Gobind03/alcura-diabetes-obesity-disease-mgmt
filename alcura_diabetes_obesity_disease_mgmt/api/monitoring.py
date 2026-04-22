"""Clinician-facing monitoring API endpoints."""

from __future__ import annotations

import frappe
from frappe import _

from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService


@frappe.whitelist()
def create_entry(
	patient: str,
	enrollment: str,
	entry_type: str,
	numeric_value: float | None = None,
	secondary_numeric_value: float | None = None,
	unit: str | None = None,
	entry_source: str = "Clinician",
	recorded_at: str | None = None,
	care_plan: str | None = None,
	source_encounter: str | None = None,
	severity: str | None = None,
	notes: str | None = None,
	medication_context: str | None = None,
	metadata_json: str | None = None,
) -> str:
	"""Create a home monitoring entry (clinician endpoint)."""
	if numeric_value is not None:
		numeric_value = float(numeric_value)
	if secondary_numeric_value is not None:
		secondary_numeric_value = float(secondary_numeric_value)

	return MonitoringService.create_entry(
		patient=patient,
		enrollment=enrollment,
		entry_type=entry_type,
		numeric_value=numeric_value,
		secondary_numeric_value=secondary_numeric_value,
		unit=unit,
		entry_source=entry_source,
		recorded_at=recorded_at,
		care_plan=care_plan,
		source_encounter=source_encounter,
		severity=severity,
		notes=notes,
		medication_context=medication_context,
		metadata_json=metadata_json,
	)


@frappe.whitelist()
def get_entries(
	patient: str,
	entry_type: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
) -> list[dict]:
	"""Retrieve monitoring entries for a patient."""
	return MonitoringService.get_entries_by_patient(
		patient=patient,
		entry_type=entry_type,
		from_date=from_date,
		to_date=to_date,
		limit=int(limit),
	)


@frappe.whitelist()
def get_latest_reading(patient: str, entry_type: str) -> dict | None:
	"""Get the most recent reading."""
	return MonitoringService.get_latest_reading(patient, entry_type)


@frappe.whitelist()
def get_chart_data(
	patient: str,
	entry_type: str,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	"""Get chart-ready data points."""
	return MonitoringService.aggregate_for_chart(
		patient=patient,
		entry_type=entry_type,
		from_date=from_date,
		to_date=to_date,
	)


@frappe.whitelist()
def supersede_entry(original_entry: str, corrected_values: str | dict = "{}") -> str:
	"""Supersede an incorrect entry with corrected values."""
	import json
	if isinstance(corrected_values, str):
		corrected_values = json.loads(corrected_values)
	return MonitoringService.supersede_entry(original_entry, corrected_values)
