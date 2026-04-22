"""Dashboard composition service — program summaries and patient cockpit."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate


class DashboardService:
	"""Composes dashboard payloads for program-level and patient-level views."""

	@staticmethod
	def get_program_summary() -> dict[str, Any]:
		"""Return program-wide statistics for the admin dashboard."""
		summary: dict[str, Any] = {
			"active_enrollments": 0,
			"by_program": {},
			"active_care_plans": 0,
			"open_alerts": 0,
			"overdue_reviews": 0,
		}

		if frappe.db.exists("DocType", "Disease Enrollment"):
			enrollments = frappe.get_all(
				"Disease Enrollment",
				filters={"program_status": "Active"},
				fields=["disease_type", "count(name) as cnt"],
				group_by="disease_type",
			)
			for e in enrollments:
				summary["by_program"][e.disease_type] = e.cnt
			summary["active_enrollments"] = sum(e.cnt for e in enrollments)

		if frappe.db.exists("DocType", "CDM Care Plan"):
			summary["active_care_plans"] = frappe.db.count(
				"CDM Care Plan", {"status": "Active"}
			)

		if frappe.db.exists("DocType", "CDM Alert"):
			summary["open_alerts"] = frappe.db.count(
				"CDM Alert", {"status": ["in", ["Open", "Acknowledged"]]}
			)

		if frappe.db.exists("DocType", "Disease Review Sheet"):
			summary["overdue_reviews"] = frappe.db.count(
				"Disease Review Sheet",
				{
					"status": "Scheduled",
					"due_date": ["<", nowdate()],
				},
			)

		return summary

	@staticmethod
	def get_patient_cockpit(patient: str) -> dict[str, Any]:
		"""Compose the full chronic disease cockpit payload for a patient.

		Returns sections: enrollment_summary, care_plan_summary, goals_summary,
		latest_measurements, medication_summary, adherence_summary,
		screening_summary, care_gaps, alerts, trend_snapshots, recent_reviews.
		"""
		cockpit: dict[str, Any] = {
			"enrollment_summary": {},
			"care_plan_summary": {},
			"goals_summary": [],
			"latest_measurements": {},
			"medication_summary": [],
			"adherence_summary": {},
			"screening_summary": [],
			"care_gaps": [],
			"alerts": [],
			"trend_snapshots": {},
			"recent_reviews": [],
		}

		enrollment = DashboardService._get_enrollment(patient)
		cockpit["enrollment_summary"] = enrollment or {}

		if not enrollment:
			return cockpit

		enrollment_name = enrollment.get("name")

		cockpit["care_plan_summary"] = DashboardService._get_care_plan(enrollment_name)
		cockpit["goals_summary"] = DashboardService._get_goals(patient)
		cockpit["latest_measurements"] = DashboardService._get_latest_measurements(patient)
		cockpit["medication_summary"] = DashboardService._get_medications(patient)
		cockpit["adherence_summary"] = DashboardService._get_adherence(patient, enrollment_name)
		cockpit["screening_summary"] = DashboardService._get_screenings(patient)
		cockpit["care_gaps"] = DashboardService._get_care_gaps(patient)
		cockpit["alerts"] = DashboardService._get_alerts(patient)
		cockpit["trend_snapshots"] = DashboardService._get_trend_snapshots(patient)
		cockpit["recent_reviews"] = DashboardService._get_recent_reviews(patient)

		return cockpit

	@staticmethod
	def get_practitioner_workload(practitioner: str) -> dict[str, Any]:
		"""Return workload metrics for a practitioner."""
		workload: dict[str, Any] = {
			"active_patients": 0,
			"pending_reviews": 0,
			"open_alerts": 0,
		}

		if frappe.db.exists("DocType", "Disease Enrollment"):
			workload["active_patients"] = frappe.db.count(
				"Disease Enrollment",
				{"practitioner": practitioner, "program_status": "Active"},
			)

		if frappe.db.exists("DocType", "Disease Review Sheet"):
			workload["pending_reviews"] = frappe.db.count(
				"Disease Review Sheet",
				{
					"practitioner": practitioner,
					"status": ["in", ["Scheduled", "Draft"]],
				},
			)

		return workload

	# ------------------------------------------------------------------
	# Private cockpit section builders
	# ------------------------------------------------------------------

	@staticmethod
	def _get_enrollment(patient: str) -> dict | None:
		if not frappe.db.exists("DocType", "Disease Enrollment"):
			return None
		return frappe.db.get_value(
			"Disease Enrollment",
			{"patient": patient, "program_status": "Active"},
			[
				"name", "disease_type", "program_status", "enrollment_date",
				"practitioner_name", "primary_clinic",
			],
			as_dict=True,
			order_by="enrollment_date desc",
		)

	@staticmethod
	def _get_care_plan(enrollment: str) -> dict:
		if not frappe.db.exists("DocType", "CDM Care Plan"):
			return {}
		plan = frappe.db.get_value(
			"CDM Care Plan",
			{"enrollment": enrollment, "status": "Active"},
			["name", "status", "start_date", "review_date", "plan_summary"],
			as_dict=True,
		)
		return plan or {}

	@staticmethod
	def _get_goals(patient: str) -> list[dict]:
		if not frappe.db.exists("DocType", "Disease Goal"):
			return []
		return frappe.get_all(
			"Disease Goal",
			filters={"patient": patient, "status": ["not in", ["Revised"]]},
			fields=[
				"name", "goal_metric", "target_value", "current_value",
				"status", "goal_type",
			],
			order_by="effective_date desc",
			limit_page_length=10,
		)

	@staticmethod
	def _get_latest_measurements(patient: str) -> dict[str, Any]:
		measurements: dict[str, Any] = {}
		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return measurements

		from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService
		for entry_type in ["Fasting Glucose", "Weight", "Blood Pressure", "Waist Circumference"]:
			reading = MonitoringService.get_latest_reading(patient, entry_type)
			if reading:
				measurements[entry_type] = reading

		return measurements

	@staticmethod
	def _get_medications(patient: str) -> list[dict]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService
			return MedicationTimelineService.get_active_medications(patient)
		except Exception:
			return []

	@staticmethod
	def _get_adherence(patient: str, enrollment: str) -> dict:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.medication import MedicationService
			return MedicationService.get_adherence_summary(patient, enrollment)
		except Exception:
			return {}

	@staticmethod
	def _get_screenings(patient: str) -> list[dict]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.screening import ScreeningService
			return ScreeningService.get_due_screenings(patient=patient)
		except Exception:
			return []

	@staticmethod
	def _get_care_gaps(patient: str) -> list[dict]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.screening import ScreeningService
			return ScreeningService.get_open_care_gaps(patient=patient)
		except Exception:
			return []

	@staticmethod
	def _get_alerts(patient: str) -> list[dict]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.alert import AlertService
			return AlertService.get_open_alerts(patient=patient)
		except Exception:
			return []

	@staticmethod
	def _get_trend_snapshots(patient: str) -> dict[str, Any]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.trends import TrendService
			return TrendService.get_multiple_series(
				patient,
				["HbA1c", "Fasting Glucose", "Weight", "Blood Pressure"],
				window="90d",
			)
		except Exception:
			return {}

	@staticmethod
	def _get_recent_reviews(patient: str) -> list[dict]:
		if not frappe.db.exists("DocType", "Disease Review Sheet"):
			return []
		return frappe.get_all(
			"Disease Review Sheet",
			filters={"patient": patient, "status": "Completed"},
			fields=["name", "review_type", "review_date", "practitioner_name"],
			order_by="review_date desc",
			limit_page_length=5,
		)
