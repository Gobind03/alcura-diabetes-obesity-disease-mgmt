"""Disease Enrollment controller.

Manages the lifecycle of a patient's enrollment in a chronic disease
management program. Enforces duplicate prevention, status transitions,
and keeps denormalised patient fields in sync.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from chronic_disease_management.constants.disease_types import SUPPORTED_DISEASE_TYPES
from chronic_disease_management.constants.statuses import EnrollmentStatus
from chronic_disease_management.utils.validators import validate_enrollment_status_transition


class DiseaseEnrollment(Document):

	def before_insert(self):
		self._validate_no_duplicate_active()

	def validate(self):
		self._validate_disease_type()
		self._validate_enrollment_date()
		self._set_patient_details()
		self._set_practitioner_name()
		self._set_default_company()

	def before_save(self):
		if self.has_value_changed("program_status") and not self.is_new():
			old_status = self.get_db_value("program_status")
			if old_status:
				validate_enrollment_status_transition(old_status, self.program_status)

	def on_update(self):
		self._sync_patient_cdm_flag()

	def on_trash(self):
		self._sync_patient_cdm_flag()

	# ------------------------------------------------------------------
	# Validation helpers
	# ------------------------------------------------------------------

	def _validate_disease_type(self) -> None:
		if self.disease_type not in SUPPORTED_DISEASE_TYPES:
			frappe.throw(
				_("Invalid disease program '{0}'. Supported: {1}").format(
					self.disease_type, ", ".join(SUPPORTED_DISEASE_TYPES)
				),
				frappe.ValidationError,
			)

	def _validate_enrollment_date(self) -> None:
		if self.enrollment_date and getdate(self.enrollment_date) > getdate(nowdate()):
			frappe.throw(
				_("Enrollment date cannot be in the future."),
				frappe.ValidationError,
			)

	def _validate_no_duplicate_active(self) -> None:
		"""Prevent duplicate active enrollments for the same patient/program."""
		if not self.patient or not self.disease_type:
			return

		existing = frappe.db.exists(
			"Disease Enrollment",
			{
				"patient": self.patient,
				"disease_type": self.disease_type,
				"program_status": ["in", [
					EnrollmentStatus.ACTIVE,
					EnrollmentStatus.DRAFT,
				]],
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("Patient {0} already has an active or draft enrollment for {1} ({2}).").format(
					self.patient, self.disease_type, existing
				),
				frappe.DuplicateEntryError,
			)

	# ------------------------------------------------------------------
	# Auto-population helpers
	# ------------------------------------------------------------------

	def _set_patient_details(self) -> None:
		if not self.patient:
			return

		if not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")

		if not self.patient_sex:
			self.patient_sex = frappe.db.get_value("Patient", self.patient, "sex")

		if not self.patient_age:
			dob = frappe.db.get_value("Patient", self.patient, "dob")
			if dob:
				from frappe.utils import date_diff

				age_days = date_diff(nowdate(), dob)
				years = age_days // 365
				self.patient_age = f"{years} years"

	def _set_practitioner_name(self) -> None:
		if self.practitioner and not self.practitioner_name:
			self.practitioner_name = frappe.db.get_value(
				"Healthcare Practitioner", self.practitioner, "practitioner_name"
			)

	def _set_default_company(self) -> None:
		if not self.company:
			try:
				self.company = frappe.db.get_single_value(
					"Disease Management Settings", "default_company"
				)
			except Exception:
				pass

	# ------------------------------------------------------------------
	# Side-effect hooks
	# ------------------------------------------------------------------

	def _sync_patient_cdm_flag(self) -> None:
		"""Keep the custom cdm_enrolled and cdm_active_programs fields on Patient in sync."""
		if not self.patient:
			return

		from chronic_disease_management.adapters.base import field_exists

		if not field_exists("Patient", "cdm_enrolled"):
			return

		active = frappe.get_all(
			"Disease Enrollment",
			filters={
				"patient": self.patient,
				"program_status": EnrollmentStatus.ACTIVE,
			},
			fields=["disease_type"],
			order_by="enrollment_date asc",
		)

		has_active = len(active) > 0
		programs_str = ", ".join(row["disease_type"] for row in active) if active else ""

		frappe.db.set_value(
			"Patient",
			self.patient,
			{
				"cdm_enrolled": int(has_active),
				"cdm_active_programs": programs_str,
			},
			update_modified=False,
		)
