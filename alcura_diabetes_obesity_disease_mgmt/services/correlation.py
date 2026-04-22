"""Correlation overlay service — combine therapy periods with outcome data."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, nowdate


class CorrelationService:
	"""Builds overlay data for visual correlation review.

	Output structure:
		base_series: primary trend data (e.g., HbA1c or glucose)
		overlay_bands: medication period bands
		event_markers: review/event points
		notes: interpretation disclaimers
	"""

	DISCLAIMER = (
		"This overlay view is for visual review support only. "
		"It does not imply causation between therapy changes and outcomes."
	)

	@staticmethod
	def get_hba1c_vs_medication(
		patient: str,
		window: str = "365d",
	) -> dict[str, Any]:
		"""HbA1c trend overlaid with medication timeline."""
		from alcura_diabetes_obesity_disease_mgmt.services.trends import TrendService
		from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService

		base = TrendService.get_trend_series(patient, "HbA1c", window)
		medications = MedicationTimelineService.get_medication_periods(patient)

		return {
			"base_series": base,
			"overlay_bands": CorrelationService._to_bands(medications),
			"event_markers": CorrelationService._get_review_markers(patient, window),
			"notes": CorrelationService.DISCLAIMER,
		}

	@staticmethod
	def get_glucose_vs_titration(
		patient: str,
		window: str = "180d",
	) -> dict[str, Any]:
		"""Glucose trend overlaid with medication changes."""
		from alcura_diabetes_obesity_disease_mgmt.services.trends import TrendService
		from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService

		base = TrendService.get_trend_series(patient, "Fasting Glucose", window)
		medications = MedicationTimelineService.get_medication_periods(patient)

		return {
			"base_series": base,
			"overlay_bands": CorrelationService._to_bands(medications),
			"event_markers": CorrelationService._get_review_markers(patient, window),
			"notes": CorrelationService.DISCLAIMER,
		}

	@staticmethod
	def get_weight_vs_medication(
		patient: str,
		window: str = "365d",
	) -> dict[str, Any]:
		"""Weight trend overlaid with anti-obesity medication periods."""
		from alcura_diabetes_obesity_disease_mgmt.services.trends import TrendService
		from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService

		base = TrendService.get_trend_series(patient, "Weight", window)
		medications = MedicationTimelineService.get_medication_periods(patient)

		return {
			"base_series": base,
			"overlay_bands": CorrelationService._to_bands(medications),
			"event_markers": CorrelationService._get_review_markers(patient, window),
			"notes": CorrelationService.DISCLAIMER,
		}

	@staticmethod
	def get_custom_overlay(
		patient: str,
		base_series_type: str,
		window: str = "180d",
	) -> dict[str, Any]:
		"""Generic overlay builder for any series type."""
		from alcura_diabetes_obesity_disease_mgmt.services.trends import TrendService
		from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService

		base = TrendService.get_trend_series(patient, base_series_type, window)
		medications = MedicationTimelineService.get_medication_periods(patient)

		return {
			"base_series": base,
			"overlay_bands": CorrelationService._to_bands(medications),
			"event_markers": CorrelationService._get_review_markers(patient, window),
			"notes": CorrelationService.DISCLAIMER,
		}

	# ------------------------------------------------------------------
	# Private helpers
	# ------------------------------------------------------------------

	@staticmethod
	def _to_bands(medication_periods: list[dict]) -> list[dict[str, Any]]:
		"""Convert medication periods to overlay band format."""
		return [
			{
				"label": p.get("medication_name", "Unknown"),
				"start": str(p["start_date"]) if p.get("start_date") else None,
				"end": str(p["stop_date"]) if p.get("stop_date") else None,
				"is_active": p.get("is_active", False),
				"dose_text": p.get("dose_text", ""),
			}
			for p in medication_periods
			if p.get("start_date")
		]

	@staticmethod
	def _get_review_markers(patient: str, window: str) -> list[dict[str, Any]]:
		"""Get review event markers for the overlay."""
		if not frappe.db.exists("DocType", "Disease Review Sheet"):
			return []

		from alcura_diabetes_obesity_disease_mgmt.services.trends import _DATE_WINDOWS
		days = _DATE_WINDOWS.get(window, 180)
		from_date = add_days(nowdate(), -days)

		reviews = frappe.get_all(
			"Disease Review Sheet",
			filters={
				"patient": patient,
				"status": "Completed",
				"review_date": [">=", from_date],
			},
			fields=["name", "review_type", "review_date"],
			order_by="review_date asc",
			limit_page_length=50,
		)

		return [
			{
				"date": str(r.review_date),
				"label": r.review_type,
				"type": "review",
			}
			for r in reviews
		]
