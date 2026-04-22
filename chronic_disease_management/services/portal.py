"""Portal service — compose patient-safe data payloads for portal pages."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate

from chronic_disease_management.permissions.cdm_permissions import get_patient_for_user


class PortalService:
	"""Composes safe data payloads for the patient portal."""

	@staticmethod
	def get_portal_context(patient: str | None = None) -> dict[str, Any]:
		"""Build the base portal context for a patient.

		Returns dict with patient info, enrollment, and feature flags.
		"""
		if not patient:
			patient = get_patient_for_user()
		if not patient:
			return {"authenticated": False}

		patient_info = frappe.db.get_value(
			"Patient", patient,
			["patient_name", "sex"],
			as_dict=True,
		)

		ctx: dict[str, Any] = {
			"authenticated": True,
			"patient": patient,
			"patient_name": patient_info.patient_name if patient_info else "",
		}

		enrollment = None
		if frappe.db.exists("DocType", "Disease Enrollment"):
			enrollment = frappe.db.get_value(
				"Disease Enrollment",
				{"patient": patient, "program_status": "Active"},
				["name", "disease_type", "enrollment_date", "practitioner_name"],
				as_dict=True,
				order_by="enrollment_date desc",
			)

		ctx["has_enrollment"] = bool(enrollment)
		ctx["enrollment"] = enrollment
		ctx["program_name"] = enrollment.disease_type if enrollment else None

		settings = frappe.get_cached_doc("Disease Management Settings")
		ctx["portal_enabled"] = bool(settings.enable_patient_portal)
		ctx["self_monitoring_enabled"] = bool(settings.allow_self_monitoring_entry)
		ctx["show_care_plan"] = bool(settings.show_care_plan_to_patient)
		ctx["show_lab_results"] = bool(settings.show_lab_results_to_patient)

		return ctx

	@staticmethod
	def get_program_page_data(patient: str) -> dict[str, Any]:
		"""Data for the My Disease Program page."""
		ctx = PortalService.get_portal_context(patient)
		if not ctx.get("has_enrollment"):
			return ctx

		enrollment = ctx["enrollment"]

		if frappe.db.exists("DocType", "CDM Care Plan"):
			care_plan = frappe.db.get_value(
				"CDM Care Plan",
				{"enrollment": enrollment.name, "status": "Active"},
				["name", "plan_summary", "start_date"],
				as_dict=True,
			)
			ctx["care_plan"] = care_plan

		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			ctx["recent_readings"] = frappe.get_all(
				"Home Monitoring Entry",
				filters={"patient": patient, "status": "Active"},
				fields=["entry_type", "numeric_value", "unit", "recorded_at"],
				order_by="recorded_at desc",
				limit_page_length=5,
			)

		return ctx

	@staticmethod
	def get_trends_page_data(patient: str) -> dict[str, Any]:
		"""Data for the My Disease Trends page."""
		ctx = PortalService.get_portal_context(patient)

		trend_types = ["Weight", "Fasting Glucose", "Blood Pressure"]
		ctx["trends"] = {}

		if frappe.db.exists("DocType", "Home Monitoring Entry"):
			from chronic_disease_management.services.monitoring import MonitoringService
			for t in trend_types:
				ctx["trends"][t] = MonitoringService.aggregate_for_chart(
					patient=patient, entry_type=t, limit=30
				)

		return ctx

	@staticmethod
	def get_goals_page_data(patient: str) -> dict[str, Any]:
		"""Data for the My Disease Goals page."""
		ctx = PortalService.get_portal_context(patient)

		if frappe.db.exists("DocType", "Disease Goal"):
			ctx["goals"] = frappe.get_all(
				"Disease Goal",
				filters={
					"patient": patient,
					"status": ["not in", ["Revised"]],
				},
				fields=[
					"goal_metric", "target_value", "target_range_low",
					"target_range_high", "target_unit", "current_value",
					"status", "effective_date", "review_date", "rationale",
				],
				order_by="effective_date desc",
			)
		else:
			ctx["goals"] = []

		return ctx

	@staticmethod
	def get_upcoming_page_data(patient: str) -> dict[str, Any]:
		"""Data for the My Upcoming Actions page."""
		ctx = PortalService.get_portal_context(patient)

		if frappe.db.exists("DocType", "Disease Review Sheet"):
			ctx["upcoming_reviews"] = frappe.get_all(
				"Disease Review Sheet",
				filters={
					"patient": patient,
					"status": ["in", ["Scheduled", "Draft"]],
				},
				fields=["review_type", "due_date", "review_date"],
				order_by="due_date asc",
				limit_page_length=5,
			)
		else:
			ctx["upcoming_reviews"] = []

		if frappe.db.exists("DocType", "Complication Screening Tracker"):
			ctx["due_screenings"] = frappe.get_all(
				"Complication Screening Tracker",
				filters={
					"patient": patient,
					"status": ["in", ["Due", "Overdue"]],
				},
				fields=["screening_type", "due_date", "status"],
				order_by="due_date asc",
				limit_page_length=5,
			)
		else:
			ctx["due_screenings"] = []

		return ctx
