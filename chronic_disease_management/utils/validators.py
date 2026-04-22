"""Shared validation helpers for CDM domain rules."""

from __future__ import annotations

import frappe
from frappe import _

from chronic_disease_management.constants.clinical import (
	CARE_PLAN_STATUS_TRANSITIONS,
	ENROLLMENT_STATUS_TRANSITIONS,
	REVIEW_STATUS_TRANSITIONS,
)
from chronic_disease_management.constants.disease_types import SUPPORTED_DISEASE_TYPES


def validate_disease_type(disease_type: str) -> None:
	"""Raise ``frappe.ValidationError`` if *disease_type* is not a supported program."""
	if disease_type not in SUPPORTED_DISEASE_TYPES:
		frappe.throw(
			_("Invalid disease type '{0}'. Must be one of: {1}").format(
				disease_type, ", ".join(SUPPORTED_DISEASE_TYPES)
			),
			frappe.ValidationError,
		)


def validate_enrollment_status_transition(current: str, target: str) -> None:
	"""Validate that moving from *current* to *target* enrollment status is allowed."""
	_validate_transition(current, target, ENROLLMENT_STATUS_TRANSITIONS, "Enrollment")


def validate_care_plan_status_transition(current: str, target: str) -> None:
	"""Validate that moving from *current* to *target* care plan status is allowed."""
	_validate_transition(current, target, CARE_PLAN_STATUS_TRANSITIONS, "Care Plan")


def validate_review_status_transition(current: str, target: str) -> None:
	"""Validate that moving from *current* to *target* review status is allowed."""
	_validate_transition(current, target, REVIEW_STATUS_TRANSITIONS, "Review")


def _validate_transition(
	current: str,
	target: str,
	transitions: dict[str, list[str]],
	label: str,
) -> None:
	allowed = transitions.get(current)
	if allowed is None:
		frappe.throw(
			_("Unknown {0} status: {1}").format(label, current),
			frappe.ValidationError,
		)
	if target not in allowed:
		frappe.throw(
			_("{0} status cannot transition from '{1}' to '{2}'. Allowed: {3}").format(
				label, current, target, ", ".join(allowed) if allowed else "none (terminal state)"
			),
			frappe.ValidationError,
		)


def validate_patient_exists(patient_id: str) -> None:
	"""Raise ``frappe.DoesNotExistError`` if the patient record is not found."""
	if not patient_id:
		frappe.throw(_("Patient ID is required."), frappe.ValidationError)
	if not frappe.db.exists("Patient", patient_id):
		frappe.throw(
			_("Patient '{0}' does not exist.").format(patient_id),
			frappe.DoesNotExistError,
		)


def validate_positive_int(value: int | None, field_label: str) -> None:
	"""Raise if *value* is not a positive integer."""
	if value is None or value < 1:
		frappe.throw(
			_("{0} must be a positive integer.").format(field_label),
			frappe.ValidationError,
		)
