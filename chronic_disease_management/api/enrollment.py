"""Whitelisted API endpoints for enrollment and baseline operations."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
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
	"""Create a new Disease Enrollment via the service layer.

	Returns:
		The name of the created enrollment document.
	"""
	from chronic_disease_management.services.enrollment import EnrollmentService

	return EnrollmentService.create_enrollment(
		patient=patient,
		disease_type=disease_type,
		practitioner=practitioner,
		enrollment_date=enrollment_date,
		source_encounter=source_encounter,
		source_appointment=source_appointment,
		primary_clinic=primary_clinic,
		notes=notes,
	)


@frappe.whitelist()
def get_active_enrollment(
	patient: str,
	disease_type: str | None = None,
) -> dict | None:
	"""Return the active enrollment for a patient, optionally filtered by program."""
	from chronic_disease_management.services.enrollment import EnrollmentService

	return EnrollmentService.get_active_enrollment(patient, disease_type)


@frappe.whitelist()
def update_enrollment_status(
	enrollment: str,
	new_status: str,
	reason: str | None = None,
) -> None:
	"""Transition an enrollment to a new status."""
	from chronic_disease_management.services.enrollment import EnrollmentService

	EnrollmentService.update_status(enrollment, new_status, reason=reason)


@frappe.whitelist()
def get_enrollment_context(
	patient: str,
	source_encounter: str | None = None,
	source_appointment: str | None = None,
) -> dict:
	"""Build a pre-fill context dict for launching enrollment from OPD records.

	Returns patient details, practitioner, and any existing enrollment warnings.
	"""
	from chronic_disease_management.services.enrollment import EnrollmentService

	return EnrollmentService.get_enrollment_context(
		patient=patient,
		source_encounter=source_encounter,
		source_appointment=source_appointment,
	)


@frappe.whitelist()
def check_existing_enrollment(
	patient: str,
	disease_type: str | None = None,
) -> list[dict]:
	"""Check for non-terminal enrollments for a patient.

	Used by the UI to warn clinicians before creating duplicates.
	"""
	from chronic_disease_management.services.enrollment import EnrollmentService

	return EnrollmentService.check_existing_enrollment(patient, disease_type)


@frappe.whitelist()
def create_baseline_assessment(enrollment: str) -> str:
	"""Create a Disease Baseline Assessment for an enrollment.

	Auto-prefills from existing healthcare data.

	Returns:
		The name of the created baseline document.
	"""
	from chronic_disease_management.services.baseline import BaselineService

	return BaselineService.create_baseline(enrollment)


@frappe.whitelist()
def refresh_baseline(
	baseline: str,
	overwrite_manual: bool = False,
) -> dict:
	"""Refresh baseline data from healthcare source records.

	Args:
		baseline: Disease Baseline Assessment document name.
		overwrite_manual: If True, overwrite clinician-curated fields too.

	Returns:
		Dict summarising which fields were refreshed.
	"""
	from chronic_disease_management.services.baseline import BaselineService

	if isinstance(overwrite_manual, str):
		overwrite_manual = overwrite_manual in ("1", "true", "True")

	return BaselineService.refresh_baseline(baseline, overwrite_manual=overwrite_manual)
