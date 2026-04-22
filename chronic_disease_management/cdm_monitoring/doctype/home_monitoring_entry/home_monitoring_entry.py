"""Home Monitoring Entry controller.

Validates patient-entered and clinician-entered longitudinal monitoring data.
Enforces entry-type-specific field requirements, value ranges, and patient/
enrollment consistency.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

_GLUCOSE_TYPES = {
	"Fasting Glucose",
	"Pre-Meal Glucose",
	"Post-Meal Glucose",
	"Bedtime Glucose",
	"Random Glucose",
}

_NUMERIC_REQUIRED_TYPES = {
	*_GLUCOSE_TYPES,
	"Weight",
	"Waist Circumference",
	"Blood Pressure",
}

_GLUCOSE_UNITS = {"mg/dL", "mmol/L"}

_DEFAULT_UNITS: dict[str, str] = {
	"Fasting Glucose": "mg/dL",
	"Pre-Meal Glucose": "mg/dL",
	"Post-Meal Glucose": "mg/dL",
	"Bedtime Glucose": "mg/dL",
	"Random Glucose": "mg/dL",
	"Weight": "kg",
	"Waist Circumference": "cm",
	"Blood Pressure": "mmHg",
}


class HomeMonitoringEntry(Document):

	def validate(self):
		self._set_date_from_recorded_at()
		self._set_entered_by()
		self._set_patient_name()
		self._validate_recorded_at()
		self._validate_enrollment_consistency()
		self._validate_numeric_requirements()
		self._validate_blood_pressure()
		self._validate_no_negative_values()
		self._set_default_unit()
		self._validate_metadata_json()

	# ------------------------------------------------------------------
	# Auto-population
	# ------------------------------------------------------------------

	def _set_date_from_recorded_at(self) -> None:
		if self.recorded_at:
			self.date = getdate(self.recorded_at)

	def _set_entered_by(self) -> None:
		if not self.entered_by_user:
			self.entered_by_user = frappe.session.user

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value("Patient", self.patient, "patient_name")

	def _set_default_unit(self) -> None:
		if not self.unit and self.entry_type in _DEFAULT_UNITS:
			self.unit = _DEFAULT_UNITS[self.entry_type]

	# ------------------------------------------------------------------
	# Validation
	# ------------------------------------------------------------------

	def _validate_recorded_at(self) -> None:
		if not self.recorded_at:
			frappe.throw(_("Recorded At is required."), frappe.ValidationError)

	def _validate_enrollment_consistency(self) -> None:
		if not self.patient or not self.enrollment:
			return
		enrollment_patient = frappe.db.get_value(
			"Disease Enrollment", self.enrollment, "patient"
		)
		if enrollment_patient and enrollment_patient != self.patient:
			frappe.throw(
				_("Patient {0} does not match enrollment {1}.").format(
					self.patient, self.enrollment
				),
				frappe.ValidationError,
			)

	def _validate_numeric_requirements(self) -> None:
		if self.entry_type in _NUMERIC_REQUIRED_TYPES:
			if self.numeric_value is None or self.numeric_value == 0:
				if self.numeric_value != 0:
					frappe.throw(
						_("Primary numeric value is required for {0}.").format(self.entry_type),
						frappe.ValidationError,
					)

	def _validate_blood_pressure(self) -> None:
		if self.entry_type == "Blood Pressure":
			if not self.numeric_value:
				frappe.throw(
					_("Systolic value (primary) is required for Blood Pressure."),
					frappe.ValidationError,
				)
			if not self.secondary_numeric_value:
				frappe.throw(
					_("Diastolic value (secondary) is required for Blood Pressure."),
					frappe.ValidationError,
				)

	def _validate_no_negative_values(self) -> None:
		if self.entry_type not in {"Hypoglycemia Event", "Hyperglycemia Event"}:
			if self.numeric_value is not None and self.numeric_value < 0:
				frappe.throw(
					_("Numeric value cannot be negative for {0}.").format(self.entry_type),
					frappe.ValidationError,
				)
			if self.secondary_numeric_value is not None and self.secondary_numeric_value < 0:
				frappe.throw(
					_("Secondary numeric value cannot be negative for {0}.").format(
						self.entry_type
					),
					frappe.ValidationError,
				)

	def _validate_metadata_json(self) -> None:
		if self.metadata_json:
			try:
				json.loads(self.metadata_json)
			except (json.JSONDecodeError, TypeError):
				frappe.throw(
					_("Metadata JSON must be valid JSON."), frappe.ValidationError
				)
