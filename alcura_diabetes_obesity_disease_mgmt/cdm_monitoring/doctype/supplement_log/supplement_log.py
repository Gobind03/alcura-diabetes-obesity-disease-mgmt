"""Supplement Log controller."""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class SupplementLog(Document):

	def validate(self):
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")
