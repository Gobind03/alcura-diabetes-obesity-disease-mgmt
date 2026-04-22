"""Disease Management Settings controller.

Single doctype that holds global configuration for the CDM app.
Access via ``get_cdm_settings()`` in ``utils.document_helpers``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from chronic_disease_management.constants.disease_types import SUPPORTED_DISEASE_TYPES


class DiseaseManagementSettings(Document):

	def validate(self):
		self._validate_enabled_programs()
		self._validate_threshold_ordering()
		self._validate_review_intervals()

	def _validate_enabled_programs(self):
		if not self.enabled_programs:
			frappe.throw(_("At least one disease program must be enabled."))
		for row in self.enabled_programs:
			if row.disease_type not in SUPPORTED_DISEASE_TYPES:
				frappe.throw(
					_("Invalid disease type '{0}'. Supported: {1}").format(
						row.disease_type, ", ".join(SUPPORTED_DISEASE_TYPES)
					)
				)
		seen = set()
		for row in self.enabled_programs:
			if row.disease_type in seen:
				frappe.throw(
					_("Duplicate disease program: {0}").format(row.disease_type)
				)
			seen.add(row.disease_type)

	def _validate_threshold_ordering(self):
		"""Warning thresholds must be lower than critical thresholds."""
		pairs = [
			("hba1c_warning_threshold", "hba1c_critical_threshold", "HbA1c"),
			("bmi_warning_threshold", "bmi_critical_threshold", "BMI"),
			("bp_systolic_warning", "bp_systolic_critical", "BP Systolic"),
			("fbs_warning_high", "fbs_critical_high", "FBS"),
		]
		for warning_field, critical_field, label in pairs:
			warning_val = self.get(warning_field) or 0
			critical_val = self.get(critical_field) or 0
			if warning_val >= critical_val:
				frappe.throw(
					_("{0} warning threshold ({1}) must be less than critical threshold ({2}).").format(
						label, warning_val, critical_val
					)
				)

	def _validate_review_intervals(self):
		interval_fields = [
			"diabetes_review_interval_days",
			"obesity_review_interval_days",
			"metabolic_review_interval_days",
		]
		for field in interval_fields:
			val = self.get(field)
			if val is not None and val < 1:
				frappe.throw(
					_("{0} must be at least 1 day.").format(self.meta.get_label(field))
				)

	def get_review_interval(self, disease_type: str) -> int:
		"""Return the configured review interval in days for a disease type."""
		mapping = {
			"Diabetes": self.diabetes_review_interval_days,
			"Obesity": self.obesity_review_interval_days,
			"Combined Metabolic": self.metabolic_review_interval_days,
		}
		interval = mapping.get(disease_type)
		if interval is None:
			frappe.throw(_("No review interval configured for disease type: {0}").format(disease_type))
		return int(interval)

	def is_program_enabled(self, disease_type: str) -> bool:
		"""Check if a specific disease program is currently enabled."""
		return any(row.disease_type == disease_type for row in (self.enabled_programs or []))

	def get_enabled_program_list(self) -> list[str]:
		"""Return list of enabled disease type strings."""
		return [row.disease_type for row in (self.enabled_programs or [])]

	def get_allowed_self_entry_types(self) -> list[str]:
		"""Return list of monitoring entry types patients can self-report."""
		if not self.allow_self_monitoring_entry:
			return []
		return [row.entry_type for row in (self.allowed_self_entry_types or [])]
