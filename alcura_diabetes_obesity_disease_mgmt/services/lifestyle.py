"""Lifestyle summary services — diet, activity, meal, supplement summaries."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, flt, nowdate


class LifestyleService:
	"""Aggregation and summary services for lifestyle monitoring data."""

	@staticmethod
	def get_diet_plan_summary(enrollment: str) -> dict[str, Any]:
		"""Return the active diet plan summary for an enrollment."""
		if not frappe.db.exists("DocType", "Diet Plan"):
			return {"has_plan": False}

		plan = frappe.db.get_value(
			"Diet Plan",
			{"enrollment": enrollment, "status": "Active"},
			[
				"name", "calorie_target", "macro_guidance",
				"carb_strategy", "effective_from", "review_date",
			],
			as_dict=True,
		)
		if not plan:
			return {"has_plan": False}

		return {"has_plan": True, **plan}

	@staticmethod
	def get_meal_adherence_summary(
		patient: str,
		lookback_days: int = 30,
	) -> dict[str, Any]:
		"""Compute meal adherence stats over a period."""
		if not frappe.db.exists("DocType", "Meal Log"):
			return {"total_logs": 0, "avg_score": None}

		from_date = add_days(nowdate(), -lookback_days)
		logs = frappe.get_all(
			"Meal Log",
			filters={
				"patient": patient,
				"logged_at": [">=", from_date],
			},
			fields=["adherence_score", "meal_type"],
		)
		total = len(logs)
		scores = [flt(l.adherence_score) for l in logs if l.adherence_score is not None]
		avg = round(sum(scores) / len(scores), 1) if scores else None

		by_meal: dict[str, int] = {}
		for l in logs:
			by_meal[l.meal_type] = by_meal.get(l.meal_type, 0) + 1

		return {
			"total_logs": total,
			"avg_score": avg,
			"by_meal_type": by_meal,
		}

	@staticmethod
	def get_activity_summary(
		patient: str,
		lookback_days: int = 30,
	) -> dict[str, Any]:
		"""Compute activity stats over a period."""
		if not frappe.db.exists("DocType", "Patient Activity Log"):
			return {"total_logs": 0, "total_minutes": 0, "total_steps": 0}

		from_date = add_days(nowdate(), -lookback_days)
		logs = frappe.get_all(
			"Patient Activity Log",
			filters={
				"patient": patient,
				"logged_at": [">=", from_date],
			},
			fields=["duration_minutes", "steps_count", "intensity"],
		)
		total = len(logs)
		total_min = sum(l.duration_minutes or 0 for l in logs)
		total_steps = sum(l.steps_count or 0 for l in logs)

		by_intensity: dict[str, int] = {}
		for l in logs:
			if l.intensity:
				by_intensity[l.intensity] = by_intensity.get(l.intensity, 0) + 1

		return {
			"total_logs": total,
			"total_minutes": total_min,
			"total_steps": total_steps,
			"by_intensity": by_intensity,
		}

	@staticmethod
	def get_supplement_summary(patient: str) -> list[dict]:
		"""Return active supplements for a patient."""
		if not frappe.db.exists("DocType", "Supplement Log"):
			return []

		return frappe.get_all(
			"Supplement Log",
			filters={
				"patient": patient,
				"end_date": ["is", "not set"],
			},
			fields=[
				"name", "supplement_name", "purpose",
				"start_date", "frequency_text",
			],
			order_by="start_date desc",
		)

	@staticmethod
	def get_lifestyle_overview(
		patient: str,
		enrollment: str | None = None,
		lookback_days: int = 30,
	) -> dict[str, Any]:
		"""Compose a full lifestyle overview."""
		overview: dict[str, Any] = {
			"diet_plan": {},
			"meal_adherence": {},
			"activity": {},
			"supplements": [],
		}
		if enrollment:
			overview["diet_plan"] = LifestyleService.get_diet_plan_summary(enrollment)
		overview["meal_adherence"] = LifestyleService.get_meal_adherence_summary(
			patient, lookback_days
		)
		overview["activity"] = LifestyleService.get_activity_summary(
			patient, lookback_days
		)
		overview["supplements"] = LifestyleService.get_supplement_summary(patient)
		return overview
