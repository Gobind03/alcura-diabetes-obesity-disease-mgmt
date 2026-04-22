"""CDM Alert controller.

Manages clinical and compliance alerts. Enforces status transitions and
records resolution metadata.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


_VALID_TRANSITIONS = {
	"Open": ["Acknowledged", "Resolved", "Dismissed"],
	"Acknowledged": ["Resolved", "Dismissed"],
	"Resolved": [],
	"Dismissed": [],
}


class CDMAlert(Document):

	def validate(self):
		self._set_patient_name()

	def before_save(self):
		if self.has_value_changed("status") and not self.is_new():
			old_status = self.get_db_value("status")
			if old_status:
				self._validate_status_transition(old_status, self.status)

	# ------------------------------------------------------------------
	# Validation
	# ------------------------------------------------------------------

	def _validate_status_transition(self, old: str, new: str) -> None:
		allowed = _VALID_TRANSITIONS.get(old, [])
		if new not in allowed:
			frappe.throw(
				_("Cannot transition alert from '{0}' to '{1}'.").format(old, new),
				frappe.ValidationError,
			)

	# ------------------------------------------------------------------
	# Auto-population
	# ------------------------------------------------------------------

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value(
				"Patient", self.patient, "patient_name"
			)
