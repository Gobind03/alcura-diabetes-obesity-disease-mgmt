"""Whitelisted API endpoints for encounter disease context and review integration."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_disease_context(patient: str, encounter: str | None = None) -> dict:
	"""Return aggregated chronic disease context for a patient.

	Used by the encounter-side CDM panel to show enrollment, care plan,
	goals, vitals, labs, medications, and care gaps in one call.

	Args:
		patient: Patient document name.
		encounter: Optional Patient Encounter document name.

	Returns:
		Dict with disease context or ``{"has_cdm_data": False}``.
	"""
	from chronic_disease_management.services.encounter_context import EncounterContextService

	return EncounterContextService.get_disease_context(patient, encounter=encounter)


@frappe.whitelist()
def get_enrollment_for_patient(patient: str) -> dict | None:
	"""Return active enrollment and care plan for a patient.

	Used by the Disease Review Sheet form to auto-populate links.

	Args:
		patient: Patient document name.

	Returns:
		Dict with ``enrollment`` and optional ``care_plan``, or None.
	"""
	enrollment = frappe.db.get_value(
		"Disease Enrollment",
		{"patient": patient, "program_status": "Active"},
		"name",
		order_by="enrollment_date desc",
	)
	if not enrollment:
		return None

	result: dict = {"enrollment": enrollment, "care_plan": None}

	if frappe.db.exists("DocType", "CDM Care Plan"):
		care_plan = frappe.db.get_value(
			"CDM Care Plan",
			{"enrollment": enrollment, "status": "Active"},
			"name",
		)
		if care_plan:
			result["care_plan"] = care_plan

	return result


@frappe.whitelist()
def create_review_from_encounter(encounter: str, review_type: str | None = None) -> str:
	"""Create or retrieve a Disease Review Sheet linked to an encounter.

	If a draft review already exists for this encounter, returns its name
	instead of creating a duplicate.

	Args:
		encounter: Patient Encounter document name.
		review_type: Optional review type override.

	Returns:
		Disease Review Sheet document name.
	"""
	from chronic_disease_management.services.review import ReviewService

	return ReviewService.create_review_from_encounter(encounter, review_type=review_type)
