"""Care Plan service — creation, lifecycle, and goal management for individualized care plans."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from chronic_disease_management.constants.statuses import GoalStatus


class CarePlanService:
	"""Manages individualized care plans linked to disease enrollments."""

	@staticmethod
	def create_care_plan(
		enrollment_id: str,
		practitioner: str | None = None,
		protocol_template: str | None = None,
	) -> str:
		"""Create a care plan for an enrollment, optionally from a protocol template.

		Args:
			enrollment_id: The Disease Enrollment to link.
			practitioner: Supervising practitioner (falls back to enrollment practitioner).
			protocol_template: Optional Protocol Template to derive goals/interventions from.

		Returns:
			The name of the newly created CDM Care Plan document.
		"""
		enrollment = frappe.get_doc("Disease Enrollment", enrollment_id)

		doc = frappe.new_doc("CDM Care Plan")
		doc.enrollment = enrollment_id
		doc.patient = enrollment.patient
		doc.disease_type = enrollment.disease_type
		doc.practitioner = practitioner or enrollment.practitioner
		if protocol_template:
			doc.protocol_template = protocol_template
		doc.insert()
		return doc.name

	@staticmethod
	def add_goal(
		care_plan_id: str,
		goal_type: str,
		goal_metric: str,
		target_value: str | None = None,
		target_range_low: float | None = None,
		target_range_high: float | None = None,
		target_unit: str | None = None,
		baseline_value: str | None = None,
		rationale: str | None = None,
		effective_date: str | None = None,
		review_date: str | None = None,
	) -> str:
		"""Add a measurable goal to a care plan as a linked Disease Goal.

		Returns:
			The name of the created Disease Goal.
		"""
		care_plan = frappe.get_doc("CDM Care Plan", care_plan_id)

		goal = frappe.new_doc("Disease Goal")
		goal.care_plan = care_plan_id
		goal.patient = care_plan.patient
		goal.goal_type = goal_type
		goal.goal_metric = goal_metric
		goal.target_value = target_value
		goal.target_range_low = target_range_low
		goal.target_range_high = target_range_high
		goal.target_unit = target_unit
		goal.baseline_value = baseline_value
		goal.rationale = rationale
		goal.effective_date = effective_date or frappe.utils.nowdate()
		goal.review_date = review_date
		goal.status = GoalStatus.NOT_STARTED
		goal.insert()
		return goal.name

	@staticmethod
	def update_goal_progress(
		goal_id: str,
		current_value: str,
		new_status: str | None = None,
	) -> None:
		"""Update the current measured value and optionally the status of a goal.

		Args:
			goal_id: The Disease Goal document name.
			current_value: Latest measurement.
			new_status: Optional new goal status.
		"""
		goal = frappe.get_doc("Disease Goal", goal_id)
		goal.current_value = current_value
		if new_status:
			goal.status = new_status
		goal.save()

	@staticmethod
	def revise_goal(
		goal_id: str,
		new_target_value: str | None = None,
		new_rationale: str | None = None,
	) -> str:
		"""Revise an existing goal, creating a new version.

		Args:
			goal_id: The Disease Goal document name to revise.
			new_target_value: Updated target.
			new_rationale: Reason for revision.

		Returns:
			The name of the newly created revised goal.
		"""
		goal = frappe.get_doc("Disease Goal", goal_id)
		return goal.revise_goal(
			new_target_value=new_target_value,
			new_rationale=new_rationale,
		)

	@staticmethod
	def get_goals_for_care_plan(
		care_plan_id: str,
		include_revised: bool = False,
	) -> list[dict]:
		"""Return goals linked to a care plan.

		Args:
			care_plan_id: CDM Care Plan document name.
			include_revised: If True, include goals with status Revised.

		Returns:
			List of goal dicts.
		"""
		if not frappe.db.exists("DocType", "Disease Goal"):
			return []

		filters: dict[str, Any] = {"care_plan": care_plan_id}
		if not include_revised:
			filters["status"] = ["!=", GoalStatus.REVISED]

		return frappe.get_all(
			"Disease Goal",
			filters=filters,
			fields=[
				"name", "goal_type", "goal_metric", "target_value",
				"target_range_low", "target_range_high", "target_unit",
				"current_value", "baseline_value", "status",
				"effective_date", "review_date", "version", "supersedes",
			],
			order_by="goal_type asc, effective_date asc",
		)

	@staticmethod
	def get_goal_history(goal_id: str) -> list[dict]:
		"""Follow the supersedes chain backwards to build the revision history.

		Returns:
			List of goal dicts ordered from oldest to newest.
		"""
		if not frappe.db.exists("DocType", "Disease Goal"):
			return []

		history: list[dict] = []
		current_id: str | None = goal_id

		visited: set[str] = set()
		while current_id and current_id not in visited:
			visited.add(current_id)
			goal = frappe.db.get_value(
				"Disease Goal",
				current_id,
				[
					"name", "goal_type", "goal_metric", "target_value",
					"current_value", "status", "effective_date", "version",
					"supersedes",
				],
				as_dict=True,
			)
			if not goal:
				break
			history.append(goal)
			current_id = goal.get("supersedes")

		history.reverse()
		return history

	@staticmethod
	def get_active_care_plan(enrollment_id: str) -> dict[str, Any] | None:
		"""Return the active care plan for an enrollment, or ``None``."""
		if not frappe.db.exists("DocType", "CDM Care Plan"):
			return None
		name = frappe.db.get_value(
			"CDM Care Plan",
			{"enrollment": enrollment_id, "status": "Active"},
			"name",
		)
		if not name:
			return None
		return frappe.get_doc("CDM Care Plan", name).as_dict()

	@staticmethod
	def get_care_plans_for_patient(patient: str) -> list[dict]:
		"""Return all care plans for a patient across enrollments."""
		if not frappe.db.exists("DocType", "CDM Care Plan"):
			return []
		return frappe.get_all(
			"CDM Care Plan",
			filters={"patient": patient},
			fields=[
				"name", "enrollment", "disease_type", "status",
				"start_date", "review_date", "practitioner_name", "creation",
			],
			order_by="creation desc",
		)
