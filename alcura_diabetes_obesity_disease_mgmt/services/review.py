"""Review service — scheduling, conducting, and recording clinical reviews.

All references use the Disease Review Sheet doctype (Story 8).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

_REVIEW_DT = "Disease Review Sheet"


class ReviewService:
	"""Manages clinical reviews for enrolled patients."""

	@staticmethod
	def schedule_review(
		enrollment_id: str,
		review_type: str,
		due_date: str,
		practitioner: str | None = None,
	) -> str:
		"""Schedule a review for an enrollment.

		Args:
			enrollment_id: The Disease Enrollment document name.
			review_type: Type of review (from DiseaseReviewType constants).
			due_date: When the review is due.
			practitioner: Optional assigned practitioner.

		Returns:
			The name of the created Disease Review Sheet.
		"""
		enrollment = frappe.get_doc("Disease Enrollment", enrollment_id)

		doc = frappe.new_doc(_REVIEW_DT)
		doc.enrollment = enrollment_id
		doc.patient = enrollment.patient
		doc.disease_type = enrollment.disease_type
		doc.review_type = review_type
		doc.due_date = due_date
		doc.review_date = due_date
		doc.practitioner = practitioner or enrollment.practitioner
		doc.status = "Scheduled"
		doc.insert()
		return doc.name

	@staticmethod
	def complete_review(
		review_id: str,
		encounter_id: str | None = None,
		clinical_impression: str | None = None,
		plan_changes: str | None = None,
		next_review_date: str | None = None,
	) -> None:
		"""Mark a review as completed, optionally linking it to a Patient Encounter.

		Args:
			review_id: The Disease Review Sheet document name.
			encounter_id: Optional Patient Encounter document name.
			clinical_impression: Optional clinical impression text.
			plan_changes: Optional plan changes text.
			next_review_date: Optional next review date.
		"""
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_review_status_transition

		doc = frappe.get_doc(_REVIEW_DT, review_id)
		validate_review_status_transition(doc.status, "Completed")
		doc.status = "Completed"
		if encounter_id:
			doc.encounter = encounter_id
		if clinical_impression:
			doc.clinical_impression = clinical_impression
		if plan_changes:
			doc.plan_changes = plan_changes
		if next_review_date:
			doc.next_review_date = next_review_date
		doc.save()

	@staticmethod
	def create_review_from_encounter(
		encounter_id: str,
		review_type: str | None = None,
	) -> str:
		"""Create a review sheet linked to a Patient Encounter.

		Auto-populates enrollment and care plan from the encounter's patient.

		Args:
			encounter_id: Patient Encounter document name.
			review_type: Optional review type; defaults based on disease type.

		Returns:
			The name of the created Disease Review Sheet.
		"""
		encounter = frappe.db.get_value(
			"Patient Encounter",
			encounter_id,
			["patient", "practitioner"],
			as_dict=True,
		)
		if not encounter:
			frappe.throw(_("Patient Encounter '{0}' not found.").format(encounter_id))

		existing_draft = frappe.db.get_value(
			_REVIEW_DT,
			{"encounter": encounter_id, "status": "Draft"},
			"name",
		)
		if existing_draft:
			return existing_draft

		doc = frappe.new_doc(_REVIEW_DT)
		doc.patient = encounter.patient
		doc.encounter = encounter_id
		doc.practitioner = encounter.practitioner
		doc.status = "Draft"

		if review_type:
			doc.review_type = review_type
		else:
			doc.review_type = ReviewService._infer_review_type(encounter.patient)

		doc.insert()
		return doc.name

	@staticmethod
	def _infer_review_type(patient: str) -> str:
		"""Infer review type from patient's active enrollment disease type."""
		enrollment = frappe.db.get_value(
			"Disease Enrollment",
			{"patient": patient, "program_status": "Active"},
			"disease_type",
			order_by="enrollment_date desc",
		)

		type_map = {
			"Diabetes": "Diabetes Follow-up",
			"Obesity": "Obesity Follow-up",
			"Combined Metabolic": "Combined Metabolic Follow-up",
			"Prediabetes / Metabolic Risk": "New Evaluation",
		}
		return type_map.get(enrollment, "New Evaluation") if enrollment else "New Evaluation"

	@staticmethod
	def get_reviews_for_enrollment(enrollment_id: str) -> list[dict]:
		"""Return all reviews for an enrollment.

		Args:
			enrollment_id: Disease Enrollment document name.

		Returns:
			List of review dicts.
		"""
		if not frappe.db.exists("DocType", _REVIEW_DT):
			return []

		return frappe.get_all(
			_REVIEW_DT,
			filters={"enrollment": enrollment_id},
			fields=[
				"name", "review_type", "status", "review_date",
				"due_date", "practitioner_name", "encounter",
			],
			order_by="review_date desc",
		)

	@staticmethod
	def get_upcoming_reviews(
		patient: str | None = None,
		practitioner: str | None = None,
		days_ahead: int = 30,
	) -> list[dict]:
		"""Return upcoming reviews within a time window.

		Args:
			patient: Optional patient filter.
			practitioner: Optional practitioner filter.
			days_ahead: Number of days to look ahead.

		Returns:
			List of review dicts.
		"""
		if not frappe.db.exists("DocType", _REVIEW_DT):
			return []

		filters: dict[str, Any] = {
			"status": ["in", ["Scheduled", "Draft"]],
			"due_date": ["<=", frappe.utils.add_days(frappe.utils.nowdate(), days_ahead)],
		}
		if patient:
			filters["patient"] = patient
		if practitioner:
			filters["practitioner"] = practitioner

		return frappe.get_all(
			_REVIEW_DT,
			filters=filters,
			fields=[
				"name", "patient", "disease_type", "review_type",
				"due_date", "practitioner", "status",
			],
			order_by="due_date asc",
		)

	@staticmethod
	def get_overdue_reviews(grace_days: int | None = None) -> list[dict]:
		"""Return reviews that are past their due date (plus optional grace period).

		Args:
			grace_days: Override grace period; defaults to settings value.

		Returns:
			List of overdue review dicts.
		"""
		if not frappe.db.exists("DocType", _REVIEW_DT):
			return []

		if grace_days is None:
			from alcura_diabetes_obesity_disease_mgmt.utils.document_helpers import get_cdm_settings
			grace_days = get_cdm_settings().missed_review_grace_days or 0

		cutoff = frappe.utils.add_days(frappe.utils.nowdate(), -grace_days)

		return frappe.get_all(
			_REVIEW_DT,
			filters={
				"status": ["in", ["Scheduled", "Draft"]],
				"due_date": ["<", cutoff],
			},
			fields=[
				"name", "patient", "disease_type", "review_type",
				"due_date", "practitioner",
			],
			order_by="due_date asc",
		)

	@staticmethod
	def get_pending_review_for_encounter(encounter_id: str) -> dict | None:
		"""Check if a draft review already exists for an encounter.

		Returns:
			Review dict or None.
		"""
		if not frappe.db.exists("DocType", _REVIEW_DT):
			return None

		return frappe.db.get_value(
			_REVIEW_DT,
			{"encounter": encounter_id, "status": ["in", ["Draft", "In Progress"]]},
			["name", "status", "review_type"],
			as_dict=True,
		)
