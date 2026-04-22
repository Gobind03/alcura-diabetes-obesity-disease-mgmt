"""Disease Review Sheet controller.

A structured review document linked to Patient Encounters for longitudinal
chronic disease follow-up. Supports partial saves, auto-linking to active
enrollment/care plan, and weight change calculation.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from chronic_disease_management.constants.statuses import CarePlanStatus, EnrollmentStatus
from chronic_disease_management.utils.validators import validate_review_status_transition


class DiseaseReviewSheet(Document):

	def validate(self):
		self._auto_link_enrollment()
		self._auto_link_care_plan()
		self._set_patient_name()
		self._set_practitioner_name()

	def before_save(self):
		if self.has_value_changed("status") and not self.is_new():
			old_status = self.get_db_value("status")
			if old_status:
				validate_review_status_transition(old_status, self.status)
		self._calculate_weight_change()

	# ------------------------------------------------------------------
	# Auto-linking
	# ------------------------------------------------------------------

	def _auto_link_enrollment(self) -> None:
		"""If patient is set but enrollment is not, find the active enrollment."""
		if self.enrollment or not self.patient:
			return

		enrollment = frappe.db.get_value(
			"Disease Enrollment",
			{
				"patient": self.patient,
				"program_status": EnrollmentStatus.ACTIVE,
			},
			["name", "disease_type"],
			as_dict=True,
			order_by="enrollment_date desc",
		)
		if enrollment:
			self.enrollment = enrollment.name
			if not self.disease_type:
				self.disease_type = enrollment.disease_type

	def _auto_link_care_plan(self) -> None:
		"""If enrollment is set but care_plan is not, find the active care plan."""
		if self.care_plan or not self.enrollment:
			return

		if not frappe.db.exists("DocType", "CDM Care Plan"):
			return

		care_plan = frappe.db.get_value(
			"CDM Care Plan",
			{
				"enrollment": self.enrollment,
				"status": CarePlanStatus.ACTIVE,
			},
			"name",
		)
		if care_plan:
			self.care_plan = care_plan

	def _set_patient_name(self) -> None:
		if self.patient and not self.patient_name:
			self.patient_name = frappe.db.get_value(
				"Patient", self.patient, "patient_name"
			)

	def _set_practitioner_name(self) -> None:
		if self.practitioner and not self.practitioner_name:
			self.practitioner_name = frappe.db.get_value(
				"Healthcare Practitioner", self.practitioner, "practitioner_name"
			)

	# ------------------------------------------------------------------
	# Weight change calculation
	# ------------------------------------------------------------------

	def _calculate_weight_change(self) -> None:
		"""Calculate weight change from previous review for the same enrollment."""
		if not self.current_weight or not self.enrollment:
			return

		prev_weight = frappe.db.get_value(
			"Disease Review Sheet",
			{
				"enrollment": self.enrollment,
				"name": ["!=", self.name or ""],
				"current_weight": [">", 0],
			},
			"current_weight",
			order_by="review_date desc, creation desc",
		)

		if prev_weight:
			self.weight_change_kg = flt(self.current_weight - flt(prev_weight), 1)
		else:
			self.weight_change_kg = 0
