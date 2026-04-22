"""Trend visualization services — standardized chart series for CDM dashboards."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, flt, nowdate


_DATE_WINDOWS = {
	"30d": 30,
	"90d": 90,
	"180d": 180,
	"365d": 365,
}


class TrendService:
	"""Reusable aggregation services for chart rendering."""

	@staticmethod
	def get_trend_series(
		patient: str,
		series_type: str,
		window: str = "90d",
		from_date: str | None = None,
		to_date: str | None = None,
	) -> dict[str, Any]:
		"""Return a standardized chart series.

		Returns:
			Dict with keys: label, unit, data_points [{x, y, y2?}],
			latest, previous, delta, trend_direction.
		"""
		method_map = {
			"HbA1c": TrendService._hba1c_series,
			"Fasting Glucose": TrendService._monitoring_series,
			"Weight": TrendService._monitoring_series,
			"BMI": TrendService._bmi_series,
			"Waist Circumference": TrendService._monitoring_series,
			"Blood Pressure": TrendService._monitoring_series,
			"Medication Adherence": TrendService._adherence_series,
		}

		resolver = method_map.get(series_type, TrendService._monitoring_series)
		from_d, to_d = TrendService._resolve_dates(window, from_date, to_date)

		result = resolver(patient, series_type, from_d, to_d)
		TrendService._compute_derived(result)
		return result

	@staticmethod
	def get_multiple_series(
		patient: str,
		series_types: list[str],
		window: str = "90d",
	) -> dict[str, dict[str, Any]]:
		"""Batch fetch multiple trend series."""
		return {
			st: TrendService.get_trend_series(patient, st, window)
			for st in series_types
		}

	# ------------------------------------------------------------------
	# Series resolvers
	# ------------------------------------------------------------------

	@staticmethod
	def _monitoring_series(
		patient: str,
		entry_type: str,
		from_date: str,
		to_date: str,
	) -> dict[str, Any]:
		"""Build series from Home Monitoring Entry."""
		unit_map = {
			"Fasting Glucose": "mg/dL",
			"Weight": "kg",
			"Waist Circumference": "cm",
			"Blood Pressure": "mmHg",
		}

		result: dict[str, Any] = {
			"label": entry_type,
			"unit": unit_map.get(entry_type, ""),
			"data_points": [],
		}

		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return result

		rows = frappe.get_all(
			"Home Monitoring Entry",
			filters={
				"patient": patient,
				"entry_type": entry_type,
				"status": "Active",
				"numeric_value": ["is", "set"],
				"recorded_at": ["between", [from_date, to_date]],
			},
			fields=["recorded_at", "numeric_value", "secondary_numeric_value"],
			order_by="recorded_at asc",
			limit_page_length=500,
		)

		for r in rows:
			point: dict[str, Any] = {"x": str(r.recorded_at), "y": flt(r.numeric_value)}
			if r.secondary_numeric_value:
				point["y2"] = flt(r.secondary_numeric_value)
			result["data_points"].append(point)

		return result

	@staticmethod
	def _hba1c_series(
		patient: str,
		series_type: str,
		from_date: str,
		to_date: str,
	) -> dict[str, Any]:
		"""Build HbA1c series from Lab Test records."""
		result: dict[str, Any] = {
			"label": "HbA1c",
			"unit": "%",
			"data_points": [],
		}

		if not frappe.db.exists("DocType", "Lab Test"):
			return result

		rows = frappe.get_all(
			"Lab Test",
			filters={
				"patient": patient,
				"template": ["like", "%HbA1c%"],
				"docstatus": 1,
				"result_date": ["between", [from_date, to_date]],
			},
			fields=["result_date", "result_value"],
			order_by="result_date asc",
			limit_page_length=100,
		)

		for r in rows:
			try:
				val = float(r.result_value)
				result["data_points"].append({"x": str(r.result_date), "y": val})
			except (ValueError, TypeError):
				continue

		return result

	@staticmethod
	def _bmi_series(
		patient: str,
		series_type: str,
		from_date: str,
		to_date: str,
	) -> dict[str, Any]:
		"""Build BMI series from Vital Signs."""
		result: dict[str, Any] = {
			"label": "BMI",
			"unit": "kg/m²",
			"data_points": [],
		}

		if not frappe.db.exists("DocType", "Vital Signs"):
			return result

		rows = frappe.get_all(
			"Vital Signs",
			filters={
				"patient": patient,
				"docstatus": 1,
				"bmi": ["is", "set"],
				"signs_date": ["between", [from_date, to_date]],
			},
			fields=["signs_date", "bmi"],
			order_by="signs_date asc",
			limit_page_length=200,
		)

		for r in rows:
			if r.bmi:
				result["data_points"].append({"x": str(r.signs_date), "y": flt(r.bmi)})

		return result

	@staticmethod
	def _adherence_series(
		patient: str,
		series_type: str,
		from_date: str,
		to_date: str,
	) -> dict[str, Any]:
		"""Build medication adherence percentage series by week."""
		result: dict[str, Any] = {
			"label": "Medication Adherence",
			"unit": "%",
			"data_points": [],
		}

		if not frappe.db.exists("DocType", "Medication Adherence Log"):
			return result

		logs = frappe.get_all(
			"Medication Adherence Log",
			filters={
				"patient": patient,
				"logged_at": ["between", [from_date, to_date]],
			},
			fields=["logged_at", "adherence_status"],
			order_by="logged_at asc",
		)

		if not logs:
			return result

		from collections import defaultdict
		weekly: dict[str, dict[str, int]] = defaultdict(lambda: {"taken": 0, "total": 0})
		for log in logs:
			week_key = str(log.logged_at)[:10]
			weekly[week_key]["total"] += 1
			if log.adherence_status == "Taken":
				weekly[week_key]["taken"] += 1

		for date_key in sorted(weekly.keys()):
			w = weekly[date_key]
			pct = round((w["taken"] / w["total"]) * 100, 1) if w["total"] else 0
			result["data_points"].append({"x": date_key, "y": pct})

		return result

	# ------------------------------------------------------------------
	# Helpers
	# ------------------------------------------------------------------

	@staticmethod
	def _resolve_dates(
		window: str,
		from_date: str | None,
		to_date: str | None,
	) -> tuple[str, str]:
		"""Resolve date range from window or explicit dates."""
		if from_date and to_date:
			return from_date, to_date
		days = _DATE_WINDOWS.get(window, 90)
		return add_days(nowdate(), -days), nowdate()

	@staticmethod
	def _compute_derived(result: dict[str, Any]) -> None:
		"""Add latest, previous, delta, trend_direction to result."""
		points = result.get("data_points", [])
		result["latest"] = None
		result["previous"] = None
		result["delta"] = None
		result["trend_direction"] = None

		if not points:
			return

		result["latest"] = points[-1]["y"]

		if len(points) >= 2:
			result["previous"] = points[-2]["y"]
			result["delta"] = round(result["latest"] - result["previous"], 2)

			if result["delta"] > 0:
				result["trend_direction"] = "Increasing"
			elif result["delta"] < 0:
				result["trend_direction"] = "Decreasing"
			else:
				result["trend_direction"] = "Stable"
