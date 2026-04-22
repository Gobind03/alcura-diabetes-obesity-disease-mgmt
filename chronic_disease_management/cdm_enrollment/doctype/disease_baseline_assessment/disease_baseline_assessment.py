"""Disease Baseline Assessment controller.

Captures a point-in-time clinical baseline linked to a Disease Enrollment.
Auto-computes BMI, obesity classification, and data completeness percentage.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


_CLINICAL_FIELDS = [
	"diagnosis_type",
	"height_cm",
	"weight_kg",
	"bmi",
	"waist_circumference_cm",
	"bp_systolic",
	"bp_diastolic",
	"pulse",
	"hba1c",
	"fasting_blood_sugar",
	"post_prandial_bs",
	"total_cholesterol",
	"ldl",
	"hdl",
	"triglycerides",
	"serum_creatinine",
	"egfr",
	"urine_microalbumin",
	"current_medications",
	"complications_summary",
	"cardiovascular_risk",
	"renal_risk",
	"lifestyle_readiness",
]

_AUTO_FETCHABLE_FIELDS = {
	"height_cm",
	"weight_kg",
	"bp_systolic",
	"bp_diastolic",
	"pulse",
	"hba1c",
	"fasting_blood_sugar",
	"post_prandial_bs",
	"total_cholesterol",
	"ldl",
	"hdl",
	"triglycerides",
	"serum_creatinine",
	"egfr",
	"urine_microalbumin",
	"current_medications",
	"vitals_source",
	"vitals_date",
	"labs_source_date",
	"medications_source_date",
}


class DiseaseBaselineAssessment(Document):

	def validate(self):
		self._validate_enrollment_unique()
		self._sync_enrollment_fields()
		self.compute_bmi()
		self.derive_obesity_class()
		self.compute_data_completeness()

	# ------------------------------------------------------------------
	# Validation
	# ------------------------------------------------------------------

	def _validate_enrollment_unique(self) -> None:
		"""Ensure only one baseline per enrollment."""
		if not self.enrollment:
			return
		existing = frappe.db.exists(
			"Disease Baseline Assessment",
			{
				"enrollment": self.enrollment,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("A baseline assessment already exists for enrollment {0} ({1}).").format(
					self.enrollment, existing
				),
				frappe.DuplicateEntryError,
			)

	def _sync_enrollment_fields(self) -> None:
		if not self.enrollment:
			return
		enrollment = frappe.db.get_value(
			"Disease Enrollment",
			self.enrollment,
			["patient", "patient_name", "disease_type"],
			as_dict=True,
		)
		if enrollment:
			self.patient = enrollment.patient
			self.patient_name = enrollment.patient_name
			self.disease_type = enrollment.disease_type

	# ------------------------------------------------------------------
	# Computed fields
	# ------------------------------------------------------------------

	def compute_bmi(self) -> None:
		"""Calculate BMI from height (cm) and weight (kg)."""
		if self.height_cm and self.weight_kg and self.height_cm > 0:
			height_m = self.height_cm / 100.0
			self.bmi = round(self.weight_kg / (height_m ** 2), 1)
		elif not self.weight_kg or not self.height_cm:
			self.bmi = 0

	def derive_obesity_class(self) -> None:
		"""Derive WHO obesity classification from BMI."""
		if not self.bmi or self.bmi <= 0:
			self.obesity_class = ""
			return

		if self.bmi < 25:
			self.obesity_class = "Normal"
		elif self.bmi < 30:
			self.obesity_class = "Overweight"
		elif self.bmi < 35:
			self.obesity_class = "Class I Obesity"
		elif self.bmi < 40:
			self.obesity_class = "Class II Obesity"
		else:
			self.obesity_class = "Class III Obesity"

	def compute_data_completeness(self) -> None:
		"""Calculate the percentage of clinical fields that have data."""
		filled = 0
		total = len(_CLINICAL_FIELDS)

		for field in _CLINICAL_FIELDS:
			value = self.get(field)
			if value is not None and value != "" and value != 0:
				filled += 1

		self.data_completeness_pct = round((filled / total) * 100, 1) if total else 0

	# ------------------------------------------------------------------
	# Public helpers (used by BaselineService)
	# ------------------------------------------------------------------

	@staticmethod
	def get_auto_fetchable_fields() -> set[str]:
		"""Return the set of field names that can be auto-populated from healthcare data."""
		return set(_AUTO_FETCHABLE_FIELDS)

	@staticmethod
	def get_clinical_fields() -> list[str]:
		"""Return the list of clinical fields tracked for completeness."""
		return list(_CLINICAL_FIELDS)
