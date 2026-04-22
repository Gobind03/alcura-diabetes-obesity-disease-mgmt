"""Care Gap controller."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class CareGap(Document):

	def validate(self):
		self._set_patient_name()
		self._auto_set_closed_date()

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")

	def _auto_set_closed_date(self) -> None:
		if self.status == "Closed" and not self.closed_on:
			self.closed_on = nowdate()
