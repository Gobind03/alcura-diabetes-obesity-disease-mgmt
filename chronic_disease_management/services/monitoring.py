"""Monitoring service — CRUD, aggregation, and supersession for Home Monitoring Entries."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, now_datetime


_DT = "Home Monitoring Entry"


class MonitoringService:
	"""Handles patient home monitoring entries: create, retrieve, aggregate, supersede."""

	@staticmethod
	def create_entry(
		patient: str,
		enrollment: str,
		entry_type: str,
		recorded_at: str | None = None,
		numeric_value: float | None = None,
		secondary_numeric_value: float | None = None,
		unit: str | None = None,
		entry_source: str = "Clinician",
		care_plan: str | None = None,
		source_encounter: str | None = None,
		severity: str | None = None,
		notes: str | None = None,
		medication_context: str | None = None,
		metadata_json: str | None = None,
		is_patient_entered: bool = False,
		related_review_sheet: str | None = None,
	) -> str:
		"""Record a home monitoring entry.

		Returns:
			The name of the created document.
		"""
		doc = frappe.new_doc(_DT)
		doc.patient = patient
		doc.enrollment = enrollment
		doc.entry_type = entry_type
		doc.recorded_at = recorded_at or now_datetime()
		doc.entry_source = entry_source
		doc.is_patient_entered = int(is_patient_entered)

		if numeric_value is not None:
			doc.numeric_value = numeric_value
		if secondary_numeric_value is not None:
			doc.secondary_numeric_value = secondary_numeric_value
		if unit:
			doc.unit = unit
		if care_plan:
			doc.care_plan = care_plan
		if source_encounter:
			doc.source_encounter = source_encounter
		if severity:
			doc.severity = severity
		if notes:
			doc.notes = notes
		if medication_context:
			doc.medication_context = medication_context
		if metadata_json:
			doc.metadata_json = metadata_json
		if related_review_sheet:
			doc.related_review_sheet = related_review_sheet

		doc.insert()
		return doc.name

	@staticmethod
	def get_entries_by_patient(
		patient: str,
		entry_type: str | None = None,
		from_date: str | None = None,
		to_date: str | None = None,
		status: str = "Active",
		limit: int = 50,
	) -> list[dict]:
		"""Fetch monitoring entries for a patient with optional filters."""
		if not frappe.db.exists("DocType", _DT):
			return []

		filters: dict[str, Any] = {"patient": patient, "status": status}
		if entry_type:
			filters["entry_type"] = entry_type

		if from_date and to_date:
			filters["recorded_at"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["recorded_at"] = [">=", from_date]
		elif to_date:
			filters["recorded_at"] = ["<=", to_date]

		return frappe.get_all(
			_DT,
			filters=filters,
			fields=[
				"name", "entry_type", "entry_source", "numeric_value",
				"secondary_numeric_value", "unit", "recorded_at", "date",
				"severity", "notes", "is_patient_entered",
			],
			order_by="recorded_at desc",
			limit_page_length=limit,
		)

	@staticmethod
	def get_entries_by_enrollment_and_type(
		enrollment: str,
		entry_type: str,
		from_date: str | None = None,
		to_date: str | None = None,
		limit: int = 100,
	) -> list[dict]:
		"""Fetch entries for a specific enrollment and entry type."""
		if not frappe.db.exists("DocType", _DT):
			return []

		filters: dict[str, Any] = {
			"enrollment": enrollment,
			"entry_type": entry_type,
			"status": "Active",
		}
		if from_date and to_date:
			filters["recorded_at"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["recorded_at"] = [">=", from_date]

		return frappe.get_all(
			_DT,
			filters=filters,
			fields=[
				"name", "numeric_value", "secondary_numeric_value",
				"unit", "recorded_at", "date", "severity", "notes",
			],
			order_by="recorded_at desc",
			limit_page_length=limit,
		)

	@staticmethod
	def get_latest_reading(patient: str, entry_type: str) -> dict | None:
		"""Return the most recent active reading for a patient and entry type."""
		if not frappe.db.exists("DocType", _DT):
			return None
		return frappe.db.get_value(
			_DT,
			{"patient": patient, "entry_type": entry_type, "status": "Active"},
			[
				"name", "numeric_value", "secondary_numeric_value",
				"unit", "recorded_at", "date", "entry_source",
			],
			as_dict=True,
			order_by="recorded_at desc",
		)

	@staticmethod
	def aggregate_for_chart(
		patient: str,
		entry_type: str,
		from_date: str | None = None,
		to_date: str | None = None,
		limit: int = 365,
	) -> list[dict]:
		"""Return data points suitable for chart rendering.

		Returns list of dicts with keys: x (recorded_at), y (numeric_value),
		y2 (secondary_numeric_value if present).
		"""
		if not frappe.db.exists("DocType", _DT):
			return []

		filters: dict[str, Any] = {
			"patient": patient,
			"entry_type": entry_type,
			"status": "Active",
			"numeric_value": ["is", "set"],
		}
		if from_date and to_date:
			filters["recorded_at"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["recorded_at"] = [">=", from_date]

		rows = frappe.get_all(
			_DT,
			filters=filters,
			fields=["recorded_at", "numeric_value", "secondary_numeric_value"],
			order_by="recorded_at asc",
			limit_page_length=limit,
		)
		result = []
		for r in rows:
			point: dict[str, Any] = {"x": r.recorded_at, "y": r.numeric_value}
			if r.secondary_numeric_value:
				point["y2"] = r.secondary_numeric_value
			result.append(point)
		return result

	@staticmethod
	def supersede_entry(
		original_entry: str,
		corrected_values: dict,
	) -> str:
		"""Supersede an incorrect entry by marking it and creating a corrected copy.

		Args:
			original_entry: Name of the entry to supersede.
			corrected_values: Dict of fields to override in the new entry.

		Returns:
			Name of the new corrected entry.
		"""
		original = frappe.get_doc(_DT, original_entry)
		if original.status != "Active":
			frappe.throw(
				_("Only active entries can be superseded."), frappe.ValidationError
			)

		original.status = "Superseded"
		original.save()

		new_doc = frappe.new_doc(_DT)
		for field in [
			"patient", "enrollment", "care_plan", "entry_type",
			"entry_source", "recorded_at", "unit", "severity",
			"medication_context", "related_review_sheet", "is_patient_entered",
		]:
			new_doc.set(field, original.get(field))

		new_doc.numeric_value = corrected_values.get("numeric_value", original.numeric_value)
		new_doc.secondary_numeric_value = corrected_values.get(
			"secondary_numeric_value", original.secondary_numeric_value
		)
		if "notes" in corrected_values:
			new_doc.notes = corrected_values["notes"]
		else:
			new_doc.notes = original.notes

		new_doc.amended_from_entry = original.name
		new_doc.entered_by_user = frappe.session.user
		new_doc.insert()
		return new_doc.name

	@staticmethod
	def get_patient_entered_entries(
		patient: str,
		limit: int = 50,
	) -> list[dict]:
		"""Fetch entries created by the patient themselves."""
		if not frappe.db.exists("DocType", _DT):
			return []

		return frappe.get_all(
			_DT,
			filters={
				"patient": patient,
				"is_patient_entered": 1,
				"status": "Active",
			},
			fields=[
				"name", "entry_type", "numeric_value",
				"secondary_numeric_value", "unit", "recorded_at", "date",
			],
			order_by="recorded_at desc",
			limit_page_length=limit,
		)
