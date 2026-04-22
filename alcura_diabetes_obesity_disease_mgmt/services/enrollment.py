"""Enrollment service — business logic for enrolling patients into CDM programs.

This service layer separates domain logic from doctype controllers.
Methods here are called by doctype events, API endpoints, and other services.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from alcura_diabetes_obesity_disease_mgmt.constants.statuses import EnrollmentStatus


class EnrollmentService:
	"""Manages the lifecycle of patient enrollment into disease management programs."""

	# ------------------------------------------------------------------
	# Creation
	# ------------------------------------------------------------------

	@staticmethod
	def create_enrollment(
		patient: str,
		disease_type: str,
		practitioner: str | None = None,
		enrollment_date: str | None = None,
		source_encounter: str | None = None,
		source_appointment: str | None = None,
		primary_clinic: str | None = None,
		notes: str | None = None,
	) -> str:
		"""Enroll a patient in a disease management program.

		Args:
			patient: Patient ID.
			disease_type: One of the supported disease types.
			practitioner: Supervising practitioner ID.
			enrollment_date: Defaults to today.
			source_encounter: Optional Patient Encounter that triggered enrollment.
			source_appointment: Optional Patient Appointment that triggered enrollment.
			primary_clinic: Optional Healthcare Service Unit.
			notes: Optional enrollment notes.

		Returns:
			The name of the newly created Disease Enrollment document.

		Raises:
			frappe.ValidationError: If validation fails (duplicate, ineligible, etc.).
		"""
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import (
			validate_disease_type,
			validate_patient_exists,
		)

		validate_patient_exists(patient)
		validate_disease_type(disease_type)

		eligibility = EnrollmentService.check_eligibility(patient, disease_type)
		if not eligibility.get("eligible"):
			frappe.throw(
				_("Patient is not eligible: {0}").format(eligibility.get("reason", "")),
				frappe.ValidationError,
			)

		doc = frappe.new_doc("Disease Enrollment")
		doc.patient = patient
		doc.disease_type = disease_type
		doc.enrollment_date = enrollment_date or frappe.utils.nowdate()

		if practitioner:
			doc.practitioner = practitioner
		if source_encounter:
			doc.source_encounter = source_encounter
		if source_appointment:
			doc.source_appointment = source_appointment
		if primary_clinic:
			doc.primary_clinic = primary_clinic
		if notes:
			doc.notes = notes

		doc.insert()
		return doc.name

	# ------------------------------------------------------------------
	# Status transitions
	# ------------------------------------------------------------------

	@staticmethod
	def update_status(
		enrollment_id: str,
		new_status: str,
		reason: str | None = None,
	) -> None:
		"""Transition an enrollment to a new status with validation.

		Args:
			enrollment_id: The Disease Enrollment document name.
			new_status: Target status.
			reason: Optional reason for the transition.
		"""
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		doc = frappe.get_doc("Disease Enrollment", enrollment_id)
		validate_enrollment_status_transition(doc.program_status, new_status)
		doc.program_status = new_status
		if reason:
			doc.status_change_reason = reason
			doc.add_comment("Info", _("Status changed to {0}: {1}").format(new_status, reason))
		doc.save()

	@staticmethod
	def close_enrollment(enrollment_id: str, reason: str | None = None) -> None:
		"""Mark an enrollment as Completed."""
		EnrollmentService.update_status(
			enrollment_id, EnrollmentStatus.COMPLETED, reason=reason
		)

	@staticmethod
	def suspend_enrollment(enrollment_id: str, reason: str | None = None) -> None:
		"""Put an enrollment On Hold."""
		EnrollmentService.update_status(
			enrollment_id, EnrollmentStatus.ON_HOLD, reason=reason
		)

	@staticmethod
	def reactivate_enrollment(enrollment_id: str) -> None:
		"""Move an On-Hold enrollment back to Active."""
		EnrollmentService.update_status(enrollment_id, EnrollmentStatus.ACTIVE)

	@staticmethod
	def withdraw_enrollment(enrollment_id: str, reason: str | None = None) -> None:
		"""Withdraw an enrollment."""
		EnrollmentService.update_status(
			enrollment_id, EnrollmentStatus.WITHDRAWN, reason=reason
		)

	# ------------------------------------------------------------------
	# Queries
	# ------------------------------------------------------------------

	@staticmethod
	def get_active_enrollments(patient: str) -> list[dict]:
		"""Return all active enrollments for a patient."""
		if not frappe.db.exists("DocType", "Disease Enrollment"):
			return []
		return frappe.get_all(
			"Disease Enrollment",
			filters={"patient": patient, "program_status": EnrollmentStatus.ACTIVE},
			fields=["name", "disease_type", "enrollment_date", "practitioner", "program_status"],
			order_by="enrollment_date desc",
		)

	@staticmethod
	def get_active_enrollment(patient: str, disease_type: str | None = None) -> dict | None:
		"""Return a single active enrollment for a patient, optionally filtered by program.

		Args:
			patient: Patient ID.
			disease_type: Optional disease type filter.

		Returns:
			Enrollment dict or None.
		"""
		if not frappe.db.exists("DocType", "Disease Enrollment"):
			return None

		filters: dict[str, Any] = {
			"patient": patient,
			"program_status": EnrollmentStatus.ACTIVE,
		}
		if disease_type:
			filters["disease_type"] = disease_type

		return frappe.db.get_value(
			"Disease Enrollment",
			filters,
			[
				"name", "disease_type", "enrollment_date",
				"practitioner", "program_status", "primary_clinic",
			],
			as_dict=True,
			order_by="enrollment_date desc",
		)

	@staticmethod
	def check_eligibility(patient: str, disease_type: str) -> dict[str, Any]:
		"""Check whether a patient can be enrolled in a disease program.

		Returns:
			Dict with ``eligible`` (bool) and ``reason`` (str).
		"""
		from alcura_diabetes_obesity_disease_mgmt.utils.document_helpers import get_enabled_programs

		enabled = get_enabled_programs()
		if disease_type not in enabled:
			return {"eligible": False, "reason": _("Program '{0}' is not enabled.").format(disease_type)}

		if frappe.db.exists("DocType", "Disease Enrollment"):
			existing = frappe.db.exists(
				"Disease Enrollment",
				{
					"patient": patient,
					"disease_type": disease_type,
					"program_status": ["in", [
						EnrollmentStatus.ACTIVE,
						EnrollmentStatus.DRAFT,
					]],
				},
			)
			if existing:
				return {"eligible": False, "reason": _("Patient already has an active enrollment.")}

		return {"eligible": True, "reason": ""}

	@staticmethod
	def check_existing_enrollment(
		patient: str,
		disease_type: str | None = None,
	) -> list[dict]:
		"""Return any non-terminal enrollments for a patient.

		Used by the OPD integration to warn clinicians before creating duplicates.
		"""
		if not frappe.db.exists("DocType", "Disease Enrollment"):
			return []

		filters: dict[str, Any] = {
			"patient": patient,
			"program_status": ["in", [
				EnrollmentStatus.DRAFT,
				EnrollmentStatus.ACTIVE,
				EnrollmentStatus.ON_HOLD,
			]],
		}
		if disease_type:
			filters["disease_type"] = disease_type

		return frappe.get_all(
			"Disease Enrollment",
			filters=filters,
			fields=[
				"name", "disease_type", "program_status",
				"enrollment_date", "practitioner_name",
			],
			order_by="enrollment_date desc",
		)

	# ------------------------------------------------------------------
	# OPD integration context builder (Story 5)
	# ------------------------------------------------------------------

	@staticmethod
	def get_enrollment_context(
		patient: str,
		source_encounter: str | None = None,
		source_appointment: str | None = None,
	) -> dict[str, Any]:
		"""Build a pre-fill context dict for launching enrollment from OPD records.

		Gathers patient details, practitioner, and clinical context from the
		source record so the enrollment form can be opened with minimal clicks.
		"""
		context: dict[str, Any] = {"patient": patient}

		patient_data = frappe.db.get_value(
			"Patient",
			patient,
			["patient_name", "sex", "dob"],
			as_dict=True,
		)
		if patient_data:
			context["patient_name"] = patient_data.get("patient_name")
			context["patient_sex"] = patient_data.get("sex")
			if patient_data.get("dob"):
				from frappe.utils import date_diff, nowdate

				age_days = date_diff(nowdate(), patient_data["dob"])
				context["patient_age"] = f"{age_days // 365} years"

		if source_encounter:
			context["source_encounter"] = source_encounter
			enc = frappe.db.get_value(
				"Patient Encounter",
				source_encounter,
				["practitioner", "practitioner_name", "medical_department"],
				as_dict=True,
			)
			if enc:
				context["practitioner"] = enc.get("practitioner")
				context["practitioner_name"] = enc.get("practitioner_name")

		if source_appointment:
			context["source_appointment"] = source_appointment
			appt = frappe.db.get_value(
				"Patient Appointment",
				source_appointment,
				["practitioner", "practitioner_name", "department"],
				as_dict=True,
			)
			if appt:
				if not context.get("practitioner"):
					context["practitioner"] = appt.get("practitioner")
					context["practitioner_name"] = appt.get("practitioner_name")

		existing = EnrollmentService.check_existing_enrollment(patient)
		context["existing_enrollments"] = existing

		return context
