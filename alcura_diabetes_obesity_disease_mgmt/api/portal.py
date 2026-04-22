"""Patient-facing secure API endpoints for the disease management portal.

All endpoints enforce patient ownership: a patient can only access their own data.
Entry types are validated against Disease Management Settings.
"""

from __future__ import annotations

import frappe
from frappe import _

from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import (
	get_patient_for_user,
	validate_portal_access,
)
from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService
from alcura_diabetes_obesity_disease_mgmt.utils.document_helpers import get_cdm_settings


@frappe.whitelist()
def create_monitoring_entry(
	entry_type: str,
	numeric_value: float | None = None,
	secondary_numeric_value: float | None = None,
	unit: str | None = None,
	recorded_at: str | None = None,
	notes: str | None = None,
	metadata_json: str | None = None,
) -> dict:
	"""Create a home monitoring entry for the logged-in patient.

	Returns:
		Dict with the created entry name and status.
	"""
	patient = _resolve_patient()
	enrollment = _resolve_active_enrollment(patient)
	_validate_allowed_entry_type(entry_type)

	if numeric_value is not None:
		numeric_value = float(numeric_value)
	if secondary_numeric_value is not None:
		secondary_numeric_value = float(secondary_numeric_value)

	name = MonitoringService.create_entry(
		patient=patient,
		enrollment=enrollment,
		entry_type=entry_type,
		numeric_value=numeric_value,
		secondary_numeric_value=secondary_numeric_value,
		unit=unit,
		recorded_at=recorded_at,
		entry_source="Patient",
		is_patient_entered=True,
		notes=notes,
		metadata_json=metadata_json,
	)

	return {"name": name, "status": "created"}


@frappe.whitelist()
def get_allowed_self_entry_types() -> list[str]:
	"""Return the list of entry types the patient is allowed to self-report."""
	settings = get_cdm_settings()
	if not settings.allow_self_monitoring_entry:
		return []

	return [
		row.entry_type
		for row in (settings.get("allowed_self_entry_types") or [])
		if row.entry_type
	]


@frappe.whitelist()
def get_my_recent_entries(
	entry_type: str | None = None,
	limit: int = 20,
) -> list[dict]:
	"""Fetch the logged-in patient's recent monitoring entries."""
	patient = _resolve_patient()
	limit = min(int(limit), 100)

	entries = MonitoringService.get_entries_by_patient(
		patient=patient,
		entry_type=entry_type,
		limit=limit,
	)

	safe_fields = [
		"name", "entry_type", "numeric_value", "secondary_numeric_value",
		"unit", "recorded_at", "date", "notes",
	]
	return [{k: e.get(k) for k in safe_fields} for e in entries]


@frappe.whitelist()
def get_my_program_summary() -> dict:
	"""Return a patient-safe program summary for the portal dashboard."""
	patient = _resolve_patient()

	summary: dict = {
		"patient": patient,
		"has_enrollment": False,
		"program_name": None,
		"enrollment_date": None,
		"practitioner_name": None,
	}

	if not frappe.db.exists("DocType", "Disease Enrollment"):
		return summary

	enrollment = frappe.db.get_value(
		"Disease Enrollment",
		{"patient": patient, "program_status": "Active"},
		["name", "disease_type", "enrollment_date", "practitioner_name"],
		as_dict=True,
		order_by="enrollment_date desc",
	)

	if not enrollment:
		return summary

	summary["has_enrollment"] = True
	summary["program_name"] = enrollment.disease_type
	summary["enrollment_date"] = enrollment.enrollment_date
	summary["practitioner_name"] = enrollment.practitioner_name

	if frappe.db.exists("DocType", "CDM Care Plan"):
		care_plan = frappe.db.get_value(
			"CDM Care Plan",
			{"enrollment": enrollment.name, "status": "Active"},
			["name", "plan_summary"],
			as_dict=True,
		)
		if care_plan:
			summary["care_plan_summary"] = care_plan.plan_summary

	return summary


@frappe.whitelist()
def get_my_goals() -> list[dict]:
	"""Return the patient's active goals in plain language."""
	patient = _resolve_patient()

	if not frappe.db.exists("DocType", "Disease Goal"):
		return []

	goals = frappe.get_all(
		"Disease Goal",
		filters={
			"patient": patient,
			"status": ["not in", ["Revised"]],
		},
		fields=[
			"goal_metric", "target_value", "target_range_low",
			"target_range_high", "target_unit", "current_value",
			"status", "effective_date", "review_date", "rationale",
		],
		order_by="effective_date desc",
	)

	return goals


@frappe.whitelist()
def get_my_upcoming_actions() -> dict:
	"""Return upcoming reviews, due labs, and overdue items."""
	patient = _resolve_patient()
	result: dict = {
		"upcoming_reviews": [],
		"due_screenings": [],
	}

	if frappe.db.exists("DocType", "Disease Review Sheet"):
		result["upcoming_reviews"] = frappe.get_all(
			"Disease Review Sheet",
			filters={
				"patient": patient,
				"status": ["in", ["Scheduled", "Draft"]],
			},
			fields=["review_type", "due_date", "review_date"],
			order_by="due_date asc",
			limit_page_length=5,
		)

	if frappe.db.exists("DocType", "Complication Screening Tracker"):
		result["due_screenings"] = frappe.get_all(
			"Complication Screening Tracker",
			filters={
				"patient": patient,
				"status": ["in", ["Due", "Overdue"]],
			},
			fields=["screening_type", "due_date", "status"],
			order_by="due_date asc",
			limit_page_length=5,
		)

	return result


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _resolve_patient() -> str:
	"""Derive the Patient record for the current session user."""
	patient = get_patient_for_user()
	if not patient:
		frappe.throw(
			_("Your account is not linked to a patient record."),
			frappe.PermissionError,
		)
	return patient


def _resolve_active_enrollment(patient: str) -> str:
	"""Find the active enrollment for the patient."""
	if not frappe.db.exists("DocType", "Disease Enrollment"):
		frappe.throw(
			_("Disease management is not configured."), frappe.ValidationError
		)

	enrollment = frappe.db.get_value(
		"Disease Enrollment",
		{"patient": patient, "program_status": "Active"},
		"name",
		order_by="enrollment_date desc",
	)
	if not enrollment:
		frappe.throw(
			_("You do not have an active disease management enrollment."),
			frappe.ValidationError,
		)
	return enrollment


def _validate_allowed_entry_type(entry_type: str) -> None:
	"""Ensure the entry type is in the allowed self-entry list."""
	allowed = get_allowed_self_entry_types()
	if entry_type not in allowed:
		frappe.throw(
			_("Entry type '{0}' is not available for self-reporting.").format(entry_type),
			frappe.ValidationError,
		)
