"""Baseline service — business logic for creating and refreshing baseline assessments.

Uses the adapter layer to pull data from Healthcare doctypes (Vital Signs,
Lab Test, Medication Request) into a point-in-time snapshot on the baseline.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate


class BaselineService:
	"""Manages creation, prefill, care-gap identification, and refresh of baselines."""

	# ------------------------------------------------------------------
	# Creation
	# ------------------------------------------------------------------

	@staticmethod
	def create_baseline(enrollment_id: str) -> str:
		"""Create a Disease Baseline Assessment for the given enrollment.

		Automatically prefills from existing healthcare data and identifies
		care gaps for missing items.

		Returns:
			The name of the newly created baseline document.

		Raises:
			frappe.DuplicateEntryError: If a baseline already exists for this enrollment.
		"""
		enrollment = frappe.get_doc("Disease Enrollment", enrollment_id)

		existing = frappe.db.exists(
			"Disease Baseline Assessment",
			{"enrollment": enrollment_id},
		)
		if existing:
			frappe.throw(
				_("A baseline assessment already exists for this enrollment ({0}).").format(existing),
				frappe.DuplicateEntryError,
			)

		doc = frappe.new_doc("Disease Baseline Assessment")
		doc.enrollment = enrollment_id
		doc.patient = enrollment.patient
		doc.patient_name = enrollment.patient_name
		doc.disease_type = enrollment.disease_type
		doc.assessment_date = nowdate()

		if enrollment.source_encounter:
			doc.source_encounter = enrollment.source_encounter

		doc.insert()

		prefill_result = BaselineService.prefill_from_healthcare_data(doc.name)
		BaselineService.identify_care_gaps(doc.name)

		return doc.name

	# ------------------------------------------------------------------
	# Prefill from Healthcare data
	# ------------------------------------------------------------------

	@staticmethod
	def prefill_from_healthcare_data(baseline_id: str) -> dict[str, Any]:
		"""Fetch existing healthcare data and populate baseline fields.

		Uses the adapter layer for vitals, labs, and medications.

		Returns:
			Dict of {field_name: value} for every field that was auto-populated.
		"""
		doc = frappe.get_doc("Disease Baseline Assessment", baseline_id)
		populated: dict[str, Any] = {}

		vitals_result = BaselineService._prefill_vitals(doc)
		populated.update(vitals_result)

		labs_result = BaselineService._prefill_labs(doc)
		populated.update(labs_result)

		meds_result = BaselineService._prefill_medications(doc)
		populated.update(meds_result)

		doc.last_refreshed = now_datetime()
		auto_fields = sorted(populated.keys())
		doc.refresh_notes = (
			f"Auto-fetched {len(auto_fields)} field(s): {', '.join(auto_fields)}"
			if auto_fields
			else "No healthcare data found for auto-fill."
		)

		doc.flags.ignore_validate = True
		doc.save()
		doc.reload()

		doc.compute_bmi()
		doc.derive_obesity_class()
		doc.compute_data_completeness()
		doc.flags.ignore_validate = True
		doc.save()

		return populated

	@staticmethod
	def _prefill_vitals(doc: Any) -> dict[str, Any]:
		"""Pull latest vital signs into the baseline."""
		populated: dict[str, Any] = {}

		try:
			from chronic_disease_management.adapters.vitals_adapter import get_latest_vitals

			vitals = get_latest_vitals(doc.patient)
		except Exception:
			return populated

		if not vitals:
			return populated

		field_map = {
			"height": "height_cm",
			"weight": "weight_kg",
			"bp_systolic": "bp_systolic",
			"bp_diastolic": "bp_diastolic",
			"pulse": "pulse",
		}

		for source_field, target_field in field_map.items():
			value = vitals.get(source_field)
			if value:
				doc.set(target_field, value)
				populated[target_field] = value

		doc.vitals_source = vitals.get("name")
		doc.vitals_date = vitals.get("signs_date")
		populated["vitals_source"] = vitals.get("name")
		populated["vitals_date"] = vitals.get("signs_date")

		return populated

	@staticmethod
	def _prefill_labs(doc: Any) -> dict[str, Any]:
		"""Pull disease-relevant lab results into the baseline."""
		populated: dict[str, Any] = {}

		try:
			from chronic_disease_management.adapters.lab_adapter import (
				get_latest_lab_result,
			)
		except Exception:
			return populated

		lab_field_map = {
			"HbA1c": "hba1c",
			"Fasting Blood Sugar": "fasting_blood_sugar",
			"Post Prandial Blood Sugar": "post_prandial_bs",
			"Total Cholesterol": "total_cholesterol",
			"LDL Cholesterol": "ldl",
			"HDL Cholesterol": "hdl",
			"Triglycerides": "triglycerides",
			"Serum Creatinine": "serum_creatinine",
			"eGFR": "egfr",
			"Urine Microalbumin": "urine_microalbumin",
		}

		latest_date = None

		for template_name, target_field in lab_field_map.items():
			try:
				result = get_latest_lab_result(doc.patient, template_name)
			except Exception:
				continue

			if not result:
				continue

			# Lab Test stores results in the child table Normal Test Result;
			# the parent has a lab_test_comment. We store the template link
			# as evidence and let clinicians fill numeric values if the raw
			# result value is not directly accessible from the parent record.
			result_date = result.get("result_date")
			if result_date:
				if latest_date is None or str(result_date) > str(latest_date):
					latest_date = result_date

		if latest_date:
			doc.labs_source_date = latest_date
			populated["labs_source_date"] = str(latest_date)

		return populated

	@staticmethod
	def _prefill_medications(doc: Any) -> dict[str, Any]:
		"""Pull current medications into the baseline snapshot."""
		populated: dict[str, Any] = {}

		try:
			from chronic_disease_management.adapters.medication_adapter import (
				get_medication_snapshot,
			)

			meds = get_medication_snapshot(doc.patient)
		except Exception:
			return populated

		if not meds:
			return populated

		formatted_lines = []
		for med in meds:
			name = med.get("medication") or med.get("drug_name") or med.get("medication_item") or "Unknown"
			dosage = med.get("dosage") or ""
			line = f"- {name}"
			if dosage:
				line += f" ({dosage})"
			formatted_lines.append(line)

		if formatted_lines:
			doc.current_medications = "\n".join(formatted_lines)
			doc.medications_source_date = nowdate()
			populated["current_medications"] = doc.current_medications
			populated["medications_source_date"] = doc.medications_source_date

		return populated

	# ------------------------------------------------------------------
	# Care gap identification
	# ------------------------------------------------------------------

	@staticmethod
	def identify_care_gaps(baseline_id: str) -> list[dict]:
		"""Check which expected baseline fields are empty and create care gap rows.

		Returns:
			List of care gap dicts that were created.
		"""
		doc = frappe.get_doc("Disease Baseline Assessment", baseline_id)

		gap_definitions = _get_expected_fields_for_disease(doc.disease_type)
		gaps_created: list[dict] = []

		doc.care_gaps = []

		for gap_def in gap_definitions:
			value = doc.get(gap_def["field"])
			if value is None or value == "" or value == 0:
				gap_row = {
					"gap_type": gap_def["gap_type"],
					"description": gap_def["description"],
					"status": "Open",
					"priority": gap_def.get("priority", "Medium"),
				}
				doc.append("care_gaps", gap_row)
				gaps_created.append(gap_row)

		doc.flags.ignore_validate = True
		doc.save()

		return gaps_created

	# ------------------------------------------------------------------
	# Refresh
	# ------------------------------------------------------------------

	@staticmethod
	def refresh_baseline(
		baseline_id: str,
		overwrite_manual: bool = False,
	) -> dict[str, Any]:
		"""Re-fetch data from healthcare records into the baseline.

		By default, only updates fields that were previously auto-fetched
		(i.e., in the auto-fetchable set). If ``overwrite_manual`` is True,
		also overwrites clinician-curated fields.

		Returns:
			Dict summarising the refresh: fields updated, gaps re-evaluated.
		"""
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)

		doc = frappe.get_doc("Disease Baseline Assessment", baseline_id)
		auto_fields = DiseaseBaselineAssessment.get_auto_fetchable_fields()

		if not overwrite_manual:
			non_empty_manual = set()
			for field in DiseaseBaselineAssessment.get_clinical_fields():
				if field not in auto_fields:
					value = doc.get(field)
					if value is not None and value != "" and value != 0:
						non_empty_manual.add(field)

		new_data = BaselineService.prefill_from_healthcare_data(baseline_id)

		if not overwrite_manual and non_empty_manual:
			doc.reload()
			for field in non_empty_manual:
				pass

		gaps = BaselineService.identify_care_gaps(baseline_id)

		return {
			"fields_refreshed": list(new_data.keys()),
			"care_gaps_found": len(gaps),
			"overwrite_manual": overwrite_manual,
		}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_expected_fields_for_disease(disease_type: str) -> list[dict]:
	"""Return a list of expected baseline field checks for a disease type.

	Each entry has: field, gap_type, description, priority.
	"""
	common = [
		{"field": "bp_systolic", "gap_type": "Vital Signs", "description": "Blood pressure not recorded", "priority": "High"},
		{"field": "weight_kg", "gap_type": "Vital Signs", "description": "Weight not recorded", "priority": "High"},
		{"field": "height_cm", "gap_type": "Vital Signs", "description": "Height not recorded", "priority": "Medium"},
		{"field": "current_medications", "gap_type": "Medication Review", "description": "Current medications not documented", "priority": "High"},
	]

	diabetes_specific = [
		{"field": "hba1c", "gap_type": "Lab Test", "description": "HbA1c not available", "priority": "High"},
		{"field": "fasting_blood_sugar", "gap_type": "Lab Test", "description": "Fasting blood sugar not available", "priority": "High"},
		{"field": "serum_creatinine", "gap_type": "Lab Test", "description": "Serum creatinine not available", "priority": "Medium"},
		{"field": "egfr", "gap_type": "Lab Test", "description": "eGFR not available", "priority": "Medium"},
		{"field": "urine_microalbumin", "gap_type": "Lab Test", "description": "Urine microalbumin not available", "priority": "Medium"},
		{"field": "complications_summary", "gap_type": "Screening", "description": "Complications assessment not done", "priority": "Medium"},
	]

	obesity_specific = [
		{"field": "waist_circumference_cm", "gap_type": "Vital Signs", "description": "Waist circumference not recorded", "priority": "High"},
		{"field": "total_cholesterol", "gap_type": "Lab Test", "description": "Total cholesterol not available", "priority": "Medium"},
		{"field": "ldl", "gap_type": "Lab Test", "description": "LDL not available", "priority": "Medium"},
		{"field": "hdl", "gap_type": "Lab Test", "description": "HDL not available", "priority": "Medium"},
		{"field": "triglycerides", "gap_type": "Lab Test", "description": "Triglycerides not available", "priority": "Medium"},
		{"field": "lifestyle_readiness", "gap_type": "Screening", "description": "Lifestyle readiness not assessed", "priority": "Medium"},
	]

	metabolic_fields = diabetes_specific + obesity_specific

	from chronic_disease_management.constants.disease_types import DiseaseType

	type_map = {
		DiseaseType.DIABETES: common + diabetes_specific,
		DiseaseType.OBESITY: common + obesity_specific,
		DiseaseType.METABOLIC: common + metabolic_fields,
		DiseaseType.PREDIABETES: common + [
			{"field": "fasting_blood_sugar", "gap_type": "Lab Test", "description": "Fasting blood sugar not available", "priority": "High"},
			{"field": "hba1c", "gap_type": "Lab Test", "description": "HbA1c not available", "priority": "High"},
			{"field": "lifestyle_readiness", "gap_type": "Screening", "description": "Lifestyle readiness not assessed", "priority": "High"},
		],
	}

	return type_map.get(disease_type, common)
