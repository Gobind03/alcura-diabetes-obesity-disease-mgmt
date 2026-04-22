"""Printable patient summary service — doctor and patient-facing formats."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate


class SummaryService:
	"""Builds printable summary payloads in both doctor and patient formats."""

	@staticmethod
	def get_doctor_summary(patient: str) -> dict[str, Any]:
		"""Full clinical summary for physician print/export.

		Sections: demographics, enrollment, care_plan, goals, latest_vitals,
		medications, adherence, screenings, care_gaps, alerts, recent_reviews.
		"""
		summary: dict[str, Any] = {
			"generated_at": nowdate(),
			"format": "doctor",
		}

		# Demographics
		patient_info = frappe.db.get_value(
			"Patient", patient,
			["patient_name", "sex", "dob"],
			as_dict=True,
		)
		summary["demographics"] = patient_info or {}

		# Enrollment
		enrollment = None
		if frappe.db.exists("DocType", "Disease Enrollment"):
			enrollment = frappe.db.get_value(
				"Disease Enrollment",
				{"patient": patient, "program_status": "Active"},
				[
					"name", "disease_type", "enrollment_date",
					"practitioner_name", "primary_clinic",
					"baseline_diagnosis_summary", "comorbidities_summary",
				],
				as_dict=True,
				order_by="enrollment_date desc",
			)
		summary["enrollment"] = enrollment or {}

		enrollment_name = enrollment.name if enrollment else None

		# Care plan
		if enrollment_name and frappe.db.exists("DocType", "CDM Care Plan"):
			summary["care_plan"] = frappe.db.get_value(
				"CDM Care Plan",
				{"enrollment": enrollment_name, "status": "Active"},
				["name", "status", "start_date", "plan_summary"],
				as_dict=True,
			) or {}
		else:
			summary["care_plan"] = {}

		# Goals
		if frappe.db.exists("DocType", "Disease Goal"):
			summary["goals"] = frappe.get_all(
				"Disease Goal",
				filters={"patient": patient, "status": ["not in", ["Revised"]]},
				fields=[
					"goal_metric", "target_value", "target_range_low",
					"target_range_high", "target_unit", "current_value",
					"status",
				],
				order_by="effective_date desc",
			)
		else:
			summary["goals"] = []

		# Latest vitals
		summary["latest_vitals"] = {}
		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService
			for entry_type in ["Fasting Glucose", "Weight", "Blood Pressure", "Waist Circumference"]:
				reading = MonitoringService.get_latest_reading(patient, entry_type)
				if reading:
					summary["latest_vitals"][entry_type] = reading

		# Medications
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.medication_timeline import MedicationTimelineService
			summary["medications"] = MedicationTimelineService.get_active_medications(patient)
		except Exception:
			summary["medications"] = []

		# Adherence
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.medication import MedicationService
			summary["adherence"] = MedicationService.get_adherence_summary(
				patient, enrollment_name
			)
		except Exception:
			summary["adherence"] = {}

		# Side effects
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.medication import MedicationService
			summary["side_effects"] = MedicationService.get_active_side_effects(patient)
		except Exception:
			summary["side_effects"] = []

		# Screenings
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.screening import ScreeningService
			summary["screenings"] = ScreeningService.get_due_screenings(patient=patient)
		except Exception:
			summary["screenings"] = []

		# Care gaps
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.screening import ScreeningService
			summary["care_gaps"] = ScreeningService.get_open_care_gaps(patient=patient)
		except Exception:
			summary["care_gaps"] = []

		# Alerts
		try:
			from alcura_diabetes_obesity_disease_mgmt.services.alert import AlertService
			summary["alerts"] = AlertService.get_open_alerts(patient=patient)
		except Exception:
			summary["alerts"] = []

		# Recent reviews
		if frappe.db.exists("DocType", "Disease Review Sheet"):
			summary["recent_reviews"] = frappe.get_all(
				"Disease Review Sheet",
				filters={"patient": patient, "status": "Completed"},
				fields=["review_type", "review_date", "practitioner_name"],
				order_by="review_date desc",
				limit_page_length=5,
			)
		else:
			summary["recent_reviews"] = []

		# Disease profiles
		if frappe.db.exists("DocType", "Diabetes Profile"):
			summary["diabetes_profile"] = frappe.db.get_value(
				"Diabetes Profile",
				{"patient": patient, "status": "Active"},
				[
					"diabetes_type", "uses_insulin", "uses_cgm",
					"hypoglycemia_awareness", "complication_summary",
				],
				as_dict=True,
			)
		else:
			summary["diabetes_profile"] = None

		if frappe.db.exists("DocType", "Obesity Profile"):
			summary["obesity_profile"] = frappe.db.get_value(
				"Obesity Profile",
				{"patient": patient, "status": "Active"},
				[
					"obesity_class", "baseline_weight", "baseline_bmi",
					"readiness_to_change",
				],
				as_dict=True,
			)
		else:
			summary["obesity_profile"] = None

		return summary

	@staticmethod
	def get_patient_summary(patient: str) -> dict[str, Any]:
		"""Simplified patient-facing summary with plain language.

		Sections: program_info, my_goals, my_readings, upcoming_actions, my_team.
		"""
		summary: dict[str, Any] = {
			"generated_at": nowdate(),
			"format": "patient",
		}

		patient_info = frappe.db.get_value(
			"Patient", patient,
			["patient_name"],
			as_dict=True,
		)
		summary["patient_name"] = patient_info.patient_name if patient_info else ""

		# Program info
		enrollment = None
		if frappe.db.exists("DocType", "Disease Enrollment"):
			enrollment = frappe.db.get_value(
				"Disease Enrollment",
				{"patient": patient, "program_status": "Active"},
				["disease_type", "enrollment_date", "practitioner_name"],
				as_dict=True,
				order_by="enrollment_date desc",
			)
		summary["program_info"] = enrollment or {}

		# Goals
		if frappe.db.exists("DocType", "Disease Goal"):
			goals = frappe.get_all(
				"Disease Goal",
				filters={"patient": patient, "status": ["not in", ["Revised"]]},
				fields=[
					"goal_metric", "target_value", "target_unit",
					"current_value", "status", "rationale",
				],
				order_by="effective_date desc",
			)
			summary["my_goals"] = goals
		else:
			summary["my_goals"] = []

		# Readings
		summary["my_readings"] = {}
		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			from alcura_diabetes_obesity_disease_mgmt.services.monitoring import MonitoringService
			for entry_type in ["Fasting Glucose", "Weight"]:
				reading = MonitoringService.get_latest_reading(patient, entry_type)
				if reading:
					summary["my_readings"][entry_type] = {
						"value": reading.get("numeric_value"),
						"unit": reading.get("unit"),
						"date": str(reading.get("date") or ""),
					}

		# Upcoming
		upcoming: dict[str, list] = {"reviews": [], "screenings": []}
		if frappe.db.exists("DocType", "Disease Review Sheet"):
			upcoming["reviews"] = frappe.get_all(
				"Disease Review Sheet",
				filters={"patient": patient, "status": ["in", ["Scheduled"]]},
				fields=["review_type", "due_date"],
				order_by="due_date asc",
				limit_page_length=3,
			)
		if frappe.db.exists("DocType", "Complication Screening Tracker"):
			upcoming["screenings"] = frappe.get_all(
				"Complication Screening Tracker",
				filters={"patient": patient, "status": ["in", ["Due", "Overdue"]]},
				fields=["screening_type", "due_date"],
				order_by="due_date asc",
				limit_page_length=3,
			)
		summary["upcoming_actions"] = upcoming

		# My team
		summary["my_team"] = {}
		if enrollment:
			summary["my_team"]["managing_doctor"] = enrollment.get("practitioner_name")

		return summary
