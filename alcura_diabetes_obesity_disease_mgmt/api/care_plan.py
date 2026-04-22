"""Whitelisted API endpoints for care plan operations."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_active_care_plan(enrollment_id: str) -> dict | None:
	"""Return the active care plan for an enrollment.

	Args:
		enrollment_id: Disease Enrollment document name.

	Returns:
		Care plan dict or None.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.get_active_care_plan(enrollment_id)


@frappe.whitelist()
def create_care_plan(
	enrollment_id: str,
	practitioner: str | None = None,
) -> str:
	"""Create a care plan for an enrollment.

	Args:
		enrollment_id: Disease Enrollment document name.
		practitioner: Optional Healthcare Practitioner.

	Returns:
		New CDM Care Plan document name.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.create_care_plan(enrollment_id, practitioner=practitioner)


@frappe.whitelist()
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
	"""Add a goal to a care plan.

	Returns:
		New Disease Goal document name.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.add_goal(
		care_plan_id=care_plan_id,
		goal_type=goal_type,
		goal_metric=goal_metric,
		target_value=target_value,
		target_range_low=float(target_range_low) if target_range_low else None,
		target_range_high=float(target_range_high) if target_range_high else None,
		target_unit=target_unit,
		baseline_value=baseline_value,
		rationale=rationale,
		effective_date=effective_date,
		review_date=review_date,
	)


@frappe.whitelist()
def revise_goal(
	goal_id: str,
	new_target_value: str | None = None,
	new_rationale: str | None = None,
) -> str:
	"""Revise an existing goal.

	Returns:
		New (revised) Disease Goal document name.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.revise_goal(
		goal_id=goal_id,
		new_target_value=new_target_value,
		new_rationale=new_rationale,
	)


@frappe.whitelist()
def get_goals(care_plan_id: str, include_revised: int = 0) -> list[dict]:
	"""Return goals for a care plan.

	Args:
		care_plan_id: CDM Care Plan document name.
		include_revised: If 1, include revised goals.

	Returns:
		List of goal dicts.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.get_goals_for_care_plan(
		care_plan_id, include_revised=bool(int(include_revised))
	)


@frappe.whitelist()
def get_goal_history(goal_id: str) -> list[dict]:
	"""Return the revision history for a goal.

	Returns:
		List of goal dicts from oldest to newest version.
	"""
	from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService

	return CarePlanService.get_goal_history(goal_id)
