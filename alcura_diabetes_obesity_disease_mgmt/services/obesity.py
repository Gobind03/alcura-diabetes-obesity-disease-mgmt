"""Obesity-specific analytics and derived logic."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, flt, nowdate


class ObesityService:
	"""Obesity-specific weight analytics, plateau/regain detection, summary."""

	@staticmethod
	def weight_change_from_baseline(enrollment: str) -> dict[str, Any]:
		"""Compute weight change from baseline for an obesity enrollment.

		Returns:
			Dict with baseline_weight, current_weight, delta, percent_change.
		"""
		result: dict[str, Any] = {
			"baseline_weight": None,
			"current_weight": None,
			"delta": None,
			"percent_change": None,
		}

		if not frappe.db.exists("DocType", "Obesity Profile"):
			return result

		profile = frappe.db.get_value(
			"Obesity Profile",
			{"enrollment": enrollment, "status": "Active"},
			["baseline_weight", "name"],
			as_dict=True,
		)
		if not profile or not profile.baseline_weight:
			return result

		result["baseline_weight"] = profile.baseline_weight

		patient = frappe.db.get_value("Disease Enrollment", enrollment, "patient")
		if not patient:
			return result

		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService

			latest = MonitoringService.get_latest_reading(patient, "Weight")
			if latest and latest.get("numeric_value"):
				current = flt(latest["numeric_value"])
				result["current_weight"] = current
				result["delta"] = round(current - profile.baseline_weight, 2)
				if profile.baseline_weight:
					result["percent_change"] = round(
						(result["delta"] / profile.baseline_weight) * 100, 2
					)

		return result

	@staticmethod
	def percent_weight_change(baseline: float, current: float) -> float | None:
		"""Calculate percent weight change."""
		if not baseline or baseline == 0:
			return None
		return round(((current - baseline) / baseline) * 100, 2)

	@staticmethod
	def detect_plateau(
		patient: str,
		lookback_days: int = 60,
		variance_threshold_kg: float = 1.0,
	) -> dict[str, Any]:
		"""Detect weight plateau (no meaningful change over period).

		Returns:
			Dict with detected (bool), readings_count, min_weight, max_weight, range.
		"""
		result: dict[str, Any] = {
			"detected": False,
			"readings_count": 0,
			"min_weight": None,
			"max_weight": None,
			"range": None,
		}

		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return result

		from_date = add_days(nowdate(), -lookback_days)
		readings = frappe.get_all(
			"Home Monitoring Entry",
			filters={
				"patient": patient,
				"entry_type": "Weight",
				"status": "Active",
				"numeric_value": ["is", "set"],
				"recorded_at": [">=", from_date],
			},
			fields=["numeric_value"],
			order_by="recorded_at desc",
		)

		if len(readings) < 3:
			return result

		values = [flt(r.numeric_value) for r in readings if r.numeric_value]
		if not values:
			return result

		min_w = min(values)
		max_w = max(values)
		weight_range = round(max_w - min_w, 2)

		result["readings_count"] = len(values)
		result["min_weight"] = round(min_w, 2)
		result["max_weight"] = round(max_w, 2)
		result["range"] = weight_range
		result["detected"] = weight_range <= variance_threshold_kg

		return result

	@staticmethod
	def detect_regain(
		patient: str,
		enrollment: str,
		regain_threshold_pct: float = 3.0,
	) -> dict[str, Any]:
		"""Detect weight regain from lowest recorded weight.

		Returns:
			Dict with detected (bool), lowest_weight, current_weight, regain_kg, regain_pct.
		"""
		result: dict[str, Any] = {
			"detected": False,
			"lowest_weight": None,
			"current_weight": None,
			"regain_kg": None,
			"regain_pct": None,
		}

		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return result

		weights = frappe.get_all(
			"Home Monitoring Entry",
			filters={
				"patient": patient,
				"enrollment": enrollment,
				"entry_type": "Weight",
				"status": "Active",
				"numeric_value": ["is", "set"],
			},
			fields=["numeric_value", "recorded_at"],
			order_by="recorded_at asc",
		)

		if len(weights) < 2:
			return result

		values_with_dates = [(flt(w.numeric_value), w.recorded_at) for w in weights if w.numeric_value]
		if not values_with_dates:
			return result

		min_val = min(v for v, _ in values_with_dates)
		current_val = values_with_dates[-1][0]

		result["lowest_weight"] = round(min_val, 2)
		result["current_weight"] = round(current_val, 2)

		if min_val > 0 and current_val > min_val:
			regain = current_val - min_val
			regain_pct = (regain / min_val) * 100
			result["regain_kg"] = round(regain, 2)
			result["regain_pct"] = round(regain_pct, 2)
			result["detected"] = regain_pct >= regain_threshold_pct

		return result

	@staticmethod
	def get_obesity_summary(enrollment: str) -> dict[str, Any]:
		"""Build a summary card for an obesity enrollment."""
		summary: dict[str, Any] = {
			"has_profile": False,
			"obesity_class": None,
			"baseline_weight": None,
			"baseline_bmi": None,
			"current_weight": None,
			"percent_change": None,
			"readiness_to_change": None,
		}

		if not frappe.db.exists("DocType", "Obesity Profile"):
			return summary

		profile = frappe.db.get_value(
			"Obesity Profile",
			{"enrollment": enrollment, "status": "Active"},
			[
				"name", "obesity_class", "baseline_weight", "baseline_bmi",
				"baseline_waist_circumference", "readiness_to_change",
			],
			as_dict=True,
		)
		if not profile:
			return summary

		summary["has_profile"] = True
		summary["obesity_class"] = profile.obesity_class
		summary["baseline_weight"] = profile.baseline_weight
		summary["baseline_bmi"] = profile.baseline_bmi
		summary["readiness_to_change"] = profile.readiness_to_change

		weight_data = ObesityService.weight_change_from_baseline(enrollment)
		summary["current_weight"] = weight_data.get("current_weight")
		summary["percent_change"] = weight_data.get("percent_change")

		return summary
