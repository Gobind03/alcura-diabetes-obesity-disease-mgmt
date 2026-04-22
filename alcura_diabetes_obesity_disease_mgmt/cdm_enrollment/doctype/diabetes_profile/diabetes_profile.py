"""Diabetes Profile controller.

One active diabetes profile per enrollment. Captures diabetes-specific
clinical data and risk flags.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class DiabetesProfile(Document):

	def before_insert(self):
		self._validate_no_duplicate_per_enrollment()

	def validate(self):
		self._set_patient_from_enrollment()
		self._set_patient_name()

	# ------------------------------------------------------------------
	# Validation
	# ------------------------------------------------------------------

	def _validate_no_duplicate_per_enrollment(self) -> None:
		if not self.enrollment:
			return
		existing = frappe.db.exists(
			"Diabetes Profile",
			{
				"enrollment": self.enrollment,
				"status": "Active",
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("Enrollment {0} already has an active Diabetes Profile ({1}).").format(
					self.enrollment, existing
				),
				frappe.DuplicateEntryError,
			)

	# ------------------------------------------------------------------
	# Auto-population
	# ------------------------------------------------------------------

	def _set_patient_from_enrollment(self) -> None:
		if self.enrollment and not self.patient:
			self.patient = frappe.db.get_value(
				"Disease Enrollment", self.enrollment, "patient"
			)

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value(
				"Patient", self.patient, "patient_name"
			)
