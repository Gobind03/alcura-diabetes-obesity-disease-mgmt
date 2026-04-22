"""Complication Screening Tracker controller."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ComplicationScreeningTracker(Document):

	def validate(self):
		self._set_patient_name()
		self._auto_mark_overdue()
		self._validate_completed_date()

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")

	def _auto_mark_overdue(self) -> None:
		if self.status == "Due" and self.due_date:
			if getdate(self.due_date) < getdate(nowdate()):
				self.status = "Overdue"

	def _validate_completed_date(self) -> None:
		if self.status == "Completed" and not self.completed_date:
			self.completed_date = nowdate()
