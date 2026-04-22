"""Encounter context service — aggregates disease management data for the encounter panel.

Provides a single-call API for clinicians to see chronic disease context
without navigating away from the Patient Encounter form.
"""

from __future__ import annotations

from typing import Any

import frappe

from alcura_diabetes_obesity_disease_mgmt.adapters.base import doctype_exists, safe_get_all


class EncounterContextService:
	"""Assembles disease management context for display within a Patient Encounter."""

	@staticmethod
	def get_disease_context(patient: str, encounter: str | None = None) -> dict[str, Any]:
		"""Return aggregated chronic disease data for a patient.

		Returns a dict with enrollment, care plan, goals, vitals, labs,
		medications, care gaps, trends, and pending review info.
		Returns ``{"has_cdm_data": False}`` if the patient has no active enrollment.
		"""
		enrollment = EncounterContextService._get_active_enrollment(patient)
		if not enrollment:
			return {"has_cdm_data": False}

		care_plan = EncounterContextService._get_active_care_plan(enrollment["name"])
		goals = EncounterContextService._get_active_goals(care_plan["name"]) if care_plan else []
		recent_vitals = EncounterContextService._get_recent_vitals(patient)
		recent_labs = EncounterContextService._get_recent_labs(patient)
		medications = EncounterContextService._get_medications(patient)
		care_gaps = EncounterContextService._get_care_gaps(enrollment["name"])
		trends = EncounterContextService._compute_trends(patient)
		pending_review = EncounterContextService._get_pending_review(patient, encounter)

		return {
			"has_cdm_data": True,
			"enrollment": enrollment,
			"care_plan": care_plan,
			"goals": goals,
			"recent_vitals": recent_vitals,
			"recent_labs": recent_labs,
			"medications": medications,
			"care_gaps": care_gaps,
			"trends": trends,
			"pending_review": pending_review,
		}

	# ------------------------------------------------------------------
	# Internal data loaders
	# ------------------------------------------------------------------

	@staticmethod
	def _get_active_enrollment(patient: str) -> dict | None:
		if not doctype_exists("Disease Enrollment"):
			return None
		return frappe.db.get_value(
			"Disease Enrollment",
			{"patient": patient, "program_status": "Active"},
			["name", "disease_type", "program_status", "enrollment_date", "practitioner_name"],
			as_dict=True,
			order_by="enrollment_date desc",
		)

	@staticmethod
	def _get_active_care_plan(enrollment_id: str) -> dict | None:
		if not doctype_exists("CDM Care Plan"):
			return None
		return frappe.db.get_value(
			"CDM Care Plan",
			{"enrollment": enrollment_id, "status": "Active"},
			["name", "status", "start_date", "review_date", "practitioner_name"],
			as_dict=True,
		)

	@staticmethod
	def _get_active_goals(care_plan_id: str) -> list[dict]:
		if not doctype_exists("Disease Goal"):
			return []
		return safe_get_all(
			"Disease Goal",
			filters={"care_plan": care_plan_id, "status": ["!=", "Revised"]},
			fields=["goal_metric", "target_value", "current_value", "status", "target_unit"],
			order_by="goal_type asc",
			limit_page_length=20,
		)

	@staticmethod
	def _get_recent_vitals(patient: str) -> dict | None:
		if not doctype_exists("Vital Signs"):
			return None
		return frappe.db.get_value(
			"Vital Signs",
			{"patient": patient, "docstatus": 1},
			["weight", "bmi", "bp_systolic", "bp_diastolic", "signs_date"],
			as_dict=True,
			order_by="signs_date desc, signs_time desc",
		)

	@staticmethod
	def _get_recent_labs(patient: str) -> dict | None:
		"""Get latest HbA1c and FBS from Lab Test results."""
		if not doctype_exists("Lab Test"):
			return None

		result: dict[str, Any] = {}

		for template_name, key in [("HbA1c", "hba1c"), ("Fasting Blood Sugar", "fbs")]:
			lab = frappe.db.get_value(
				"Lab Test",
				{
					"patient": patient,
					"docstatus": 1,
					"template": template_name,
				},
				["result_value", "result_date"],
				as_dict=True,
				order_by="result_date desc",
			)
			if lab:
				result[key] = lab.get("result_value")
				result[f"{key}_date"] = lab.get("result_date")

		return result if result else None

	@staticmethod
	def _get_medications(patient: str) -> list[dict]:
		try:
			from alcura_diabetes_obesity_disease_mgmt.adapters.medication_adapter import get_current_medications
			meds = get_current_medications(patient)
			return [
				{"medication": m.get("medication") or m.get("drug_name", ""), "status": m.get("status", "")}
				for m in meds[:10]
			]
		except Exception:
			return []

	@staticmethod
	def _get_care_gaps(enrollment_id: str) -> list[dict]:
		if not doctype_exists("Disease Baseline Assessment"):
			return []

		baseline = frappe.db.get_value(
			"Disease Baseline Assessment",
			{"enrollment": enrollment_id},
			"name",
		)
		if not baseline:
			return []

		return safe_get_all(
			"Baseline Care Gap",
			filters={"parent": baseline, "status": ["in", ["Open", "In Progress"]]},
			fields=["description", "status", "priority"],
			limit_page_length=10,
		)

	@staticmethod
	def _compute_trends(patient: str) -> dict[str, str]:
		"""Compute simple trends by comparing last two values."""
		trends: dict[str, str] = {}

		if doctype_exists("Vital Signs"):
			weights = frappe.get_all(
				"Vital Signs",
				filters={"patient": patient, "docstatus": 1, "weight": [">", 0]},
				fields=["weight"],
				order_by="signs_date desc",
				limit_page_length=2,
			)
			if len(weights) >= 2:
				if weights[0]["weight"] < weights[1]["weight"]:
					trends["weight_trend"] = "decreasing"
				elif weights[0]["weight"] > weights[1]["weight"]:
					trends["weight_trend"] = "increasing"
				else:
					trends["weight_trend"] = "stable"

		if doctype_exists("Lab Test"):
			hba1c_values = frappe.get_all(
				"Lab Test",
				filters={"patient": patient, "docstatus": 1, "template": "HbA1c"},
				fields=["result_value"],
				order_by="result_date desc",
				limit_page_length=2,
			)
			if len(hba1c_values) >= 2:
				try:
					v0 = float(hba1c_values[0]["result_value"])
					v1 = float(hba1c_values[1]["result_value"])
					if v0 < v1:
						trends["hba1c_trend"] = "improving"
					elif v0 > v1:
						trends["hba1c_trend"] = "worsening"
					else:
						trends["hba1c_trend"] = "stable"
				except (ValueError, TypeError):
					pass

		return trends

	@staticmethod
	def _get_pending_review(patient: str, encounter: str | None = None) -> dict | None:
		if not doctype_exists("Disease Review Sheet"):
			return None

		if encounter:
			review = frappe.db.get_value(
				"Disease Review Sheet",
				{"encounter": encounter, "status": ["in", ["Draft", "In Progress"]]},
				["name", "due_date", "review_type", "status"],
				as_dict=True,
			)
			if review:
				return review

		return frappe.db.get_value(
			"Disease Review Sheet",
			{
				"patient": patient,
				"status": ["in", ["Scheduled", "Draft"]],
			},
			["name", "due_date", "review_type", "status"],
			as_dict=True,
			order_by="due_date asc",
		)
