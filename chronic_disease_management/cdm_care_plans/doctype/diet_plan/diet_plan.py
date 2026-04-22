"""Diet Plan controller."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class DietPlan(Document):

	def validate(self):
		self._set_patient_name()
		self._set_patient_from_enrollment()

	def _set_patient_from_enrollment(self) -> None:
		if self.enrollment and not self.patient:
			self.patient = frappe.db.get_value(
				"Disease Enrollment", self.enrollment, "patient"
			)

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")
