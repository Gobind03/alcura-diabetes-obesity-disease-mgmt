"""Medication Side Effect Log controller."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class MedicationSideEffectLog(Document):

	def validate(self):
		self._set_patient_name()
		self._set_entered_by()
		self._validate_enrollment_consistency()
		self._validate_resolved_date()

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")

	def _set_entered_by(self) -> None:
		if not self.entered_by_user:
			self.entered_by_user = frappe.session.user

	def _validate_enrollment_consistency(self) -> None:
		if not self.patient or not self.enrollment:
			return
		enrollment_patient = frappe.db.get_value(
			"Disease Enrollment", self.enrollment, "patient"
		)
		if enrollment_patient and enrollment_patient != self.patient:
			frappe.throw(
				_("Patient does not match enrollment."), frappe.ValidationError
			)

	def _validate_resolved_date(self) -> None:
		if self.resolved_date and self.onset_date:
			from frappe.utils import getdate
			if getdate(self.resolved_date) < getdate(self.onset_date):
				frappe.throw(
					_("Resolved date cannot be before onset date."),
					frappe.ValidationError,
				)
