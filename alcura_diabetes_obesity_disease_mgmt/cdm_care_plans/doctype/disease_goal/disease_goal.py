"""Disease Goal controller.

Each goal is a linked document under a CDM Care Plan. Supports revision-based
versioning: revising a goal marks it as "Revised" and creates a successor with
a ``supersedes`` back-link, preserving the full audit trail.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from alcura_diabetes_obesity_disease_mgmt.constants.statuses import GoalStatus


class DiseaseGoal(Document):

	def validate(self):
		self._set_patient_from_care_plan()
		self._validate_target()
		self._validate_effective_date()

	def on_update(self):
		self._refresh_care_plan_goals_html()

	def on_trash(self):
		self._refresh_care_plan_goals_html()

	# ------------------------------------------------------------------
	# Validation helpers
	# ------------------------------------------------------------------

	def _set_patient_from_care_plan(self) -> None:
		if self.care_plan and not self.patient:
			self.patient = frappe.db.get_value(
				"CDM Care Plan", self.care_plan, "patient"
			)

	def _validate_target(self) -> None:
		"""Require at least a target_value or both range bounds."""
		has_single = bool(self.target_value)
		has_range = (
			self.target_range_low is not None
			and self.target_range_high is not None
			and self.target_range_low != 0
			and self.target_range_high != 0
		)
		if not has_single and not has_range:
			frappe.throw(
				_("Provide either a Target Value or both Target Range Low and High."),
				frappe.ValidationError,
			)
		if has_range and self.target_range_low >= self.target_range_high:
			frappe.throw(
				_("Target Range Low must be less than Target Range High."),
				frappe.ValidationError,
			)

	def _validate_effective_date(self) -> None:
		if self.effective_date and getdate(self.effective_date) > getdate(nowdate()):
			frappe.throw(
				_("Effective date cannot be in the future."),
				frappe.ValidationError,
			)

	# ------------------------------------------------------------------
	# Goal revision
	# ------------------------------------------------------------------

	@frappe.whitelist()
	def revise_goal(
		self,
		new_target_value: str | None = None,
		new_target_range_low: float | None = None,
		new_target_range_high: float | None = None,
		new_rationale: str | None = None,
	) -> str:
		"""Create a revised version of this goal.

		Marks the current goal as Revised and creates a new Disease Goal
		linked via ``supersedes``.

		Returns:
			Name of the newly created goal.
		"""
		if self.status == GoalStatus.REVISED:
			frappe.throw(
				_("This goal has already been revised."),
				frappe.ValidationError,
			)

		self.status = GoalStatus.REVISED
		self.save()

		new_goal = frappe.new_doc("Disease Goal")
		new_goal.care_plan = self.care_plan
		new_goal.patient = self.patient
		new_goal.goal_type = self.goal_type
		new_goal.goal_metric = self.goal_metric
		new_goal.target_value = new_target_value or self.target_value
		new_goal.target_range_low = new_target_range_low if new_target_range_low is not None else self.target_range_low
		new_goal.target_range_high = new_target_range_high if new_target_range_high is not None else self.target_range_high
		new_goal.target_unit = self.target_unit
		new_goal.baseline_value = self.current_value or self.baseline_value
		new_goal.rationale = new_rationale or self.rationale
		new_goal.effective_date = nowdate()
		new_goal.review_date = self.review_date
		new_goal.status = GoalStatus.NOT_STARTED
		new_goal.version = (self.version or 1) + 1
		new_goal.supersedes = self.name
		new_goal.insert()

		return new_goal.name

	# ------------------------------------------------------------------
	# Side effects
	# ------------------------------------------------------------------

	def _refresh_care_plan_goals_html(self) -> None:
		if not self.care_plan:
			return
		try:
			care_plan = frappe.get_doc("CDM Care Plan", self.care_plan)
			care_plan.render_goals_html()
		except frappe.DoesNotExistError:
			pass
