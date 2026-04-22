"""Diabetes-specific analytics and derived logic."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


class DiabetesService:
	"""Diabetes-specific detection, summary, and flag services."""

	@staticmethod
	def detect_recurrent_hypoglycemia(
		patient: str,
		lookback_days: int = 30,
		threshold_count: int = 3,
	) -> dict[str, Any]:
		"""Check for recurrent hypoglycemia events in the lookback window.

		Returns:
			Dict with keys: detected (bool), count (int), events (list).
		"""
		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return {"detected": False, "count": 0, "events": []}

		from_date = add_days(nowdate(), -lookback_days)
		events = frappe.get_all(
			"Home Monitoring Entry",
			filters={
				"patient": patient,
				"entry_type": "Hypoglycemia Event",
				"status": "Active",
				"recorded_at": [">=", from_date],
			},
			fields=["name", "numeric_value", "severity", "recorded_at"],
			order_by="recorded_at desc",
		)
		return {
			"detected": len(events) >= threshold_count,
			"count": len(events),
			"events": events,
		}

	@staticmethod
	def detect_repeated_high_fasting(
		patient: str,
		lookback_days: int = 30,
		threshold_mg_dl: float = 130.0,
		threshold_count: int = 3,
	) -> dict[str, Any]:
		"""Detect repeated high fasting glucose readings.

		Returns:
			Dict with keys: detected (bool), count (int), readings (list).
		"""
		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return {"detected": False, "count": 0, "readings": []}

		from_date = add_days(nowdate(), -lookback_days)
		readings = frappe.get_all(
			"Home Monitoring Entry",
			filters={
				"patient": patient,
				"entry_type": "Fasting Glucose",
				"status": "Active",
				"numeric_value": [">=", threshold_mg_dl],
				"recorded_at": [">=", from_date],
			},
			fields=["name", "numeric_value", "unit", "recorded_at"],
			order_by="recorded_at desc",
		)
		return {
			"detected": len(readings) >= threshold_count,
			"count": len(readings),
			"readings": readings,
		}

	@staticmethod
	def get_diabetes_summary(enrollment: str) -> dict[str, Any]:
		"""Build a summary card for a diabetes enrollment.

		Returns:
			Dict with profile info, latest readings, and flag counts.
		"""
		summary: dict[str, Any] = {
			"has_profile": False,
			"diabetes_type": None,
			"uses_insulin": False,
			"risk_flags": [],
			"latest_hba1c": None,
			"latest_fasting_glucose": None,
		}

		if not frappe.db.exists("DocType", "Diabetes Profile"):
			return summary

		profile = frappe.db.get_value(
			"Diabetes Profile",
			{"enrollment": enrollment, "status": "Active"},
			[
				"name", "diabetes_type", "uses_insulin", "uses_cgm",
				"hypoglycemia_awareness", "renal_risk_flag", "cvd_risk_flag",
				"foot_risk_flag", "retinopathy_flag", "neuropathy_flag",
			],
			as_dict=True,
		)
		if not profile:
			return summary

		summary["has_profile"] = True
		summary["diabetes_type"] = profile.diabetes_type
		summary["uses_insulin"] = bool(profile.uses_insulin)

		flags = []
		for flag_field in ["renal_risk_flag", "cvd_risk_flag", "foot_risk_flag",
						   "retinopathy_flag", "neuropathy_flag"]:
			if profile.get(flag_field):
				flags.append(flag_field.replace("_flag", "").replace("_", " ").title())
		summary["risk_flags"] = flags

		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			patient = frappe.db.get_value("Disease Enrollment", enrollment, "patient")
			if patient:
				from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService

				fasting = MonitoringService.get_latest_reading(patient, "Fasting Glucose")
				if fasting:
					summary["latest_fasting_glucose"] = fasting

		return summary

	@staticmethod
	def get_unresolved_flags(enrollment: str) -> list[str]:
		"""Return list of active risk flag names for a diabetes enrollment."""
		if not frappe.db.exists("DocType", "Diabetes Profile"):
			return []

		profile = frappe.db.get_value(
			"Diabetes Profile",
			{"enrollment": enrollment, "status": "Active"},
			[
				"renal_risk_flag", "cvd_risk_flag", "foot_risk_flag",
				"retinopathy_flag", "neuropathy_flag",
			],
			as_dict=True,
		)
		if not profile:
			return []

		return [
			field.replace("_flag", "").replace("_", " ").title()
			for field in [
				"renal_risk_flag", "cvd_risk_flag", "foot_risk_flag",
				"retinopathy_flag", "neuropathy_flag",
			]
			if profile.get(field)
		]

	@staticmethod
	def get_monitoring_snapshot(
		patient: str,
		lookback_days: int = 90,
	) -> dict[str, Any]:
		"""Return a quick monitoring data snapshot for the diabetes patient."""
		snapshot: dict[str, Any] = {
			"glucose_entries_count": 0,
			"hypo_events_count": 0,
			"hyper_events_count": 0,
		}

		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return snapshot

		from_date = add_days(nowdate(), -lookback_days)
		glucose_types = [
			"Fasting Glucose", "Pre-Meal Glucose", "Post-Meal Glucose",
			"Bedtime Glucose", "Random Glucose",
		]
		snapshot["glucose_entries_count"] = frappe.db.count(
			"Home Monitoring Entry",
			{
				"patient": patient,
				"entry_type": ["in", glucose_types],
				"status": "Active",
				"recorded_at": [">=", from_date],
			},
		)
		snapshot["hypo_events_count"] = frappe.db.count(
			"Home Monitoring Entry",
			{
				"patient": patient,
				"entry_type": "Hypoglycemia Event",
				"status": "Active",
				"recorded_at": [">=", from_date],
			},
		)
		snapshot["hyper_events_count"] = frappe.db.count(
			"Home Monitoring Entry",
			{
				"patient": patient,
				"entry_type": "Hyperglycemia Event",
				"status": "Active",
				"recorded_at": [">=", from_date],
			},
		)
		return snapshot
