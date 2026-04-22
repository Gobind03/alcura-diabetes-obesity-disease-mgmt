"""Tests for Disease Baseline Assessment doctype and BaselineService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest

from chronic_disease_management.constants.disease_types import DiseaseType


# ---------------------------------------------------------------------------
# Controller tests (BMI, obesity class, data completeness)
# ---------------------------------------------------------------------------

class TestBaselineAssessmentBMI:
	"""Test BMI auto-calculation in the controller."""

	def _make_doc(self, **kwargs):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = MagicMock(spec=DiseaseBaselineAssessment)
		doc.height_cm = kwargs.get("height_cm", 0)
		doc.weight_kg = kwargs.get("weight_kg", 0)
		doc.bmi = 0
		doc.obesity_class = ""

		def mock_get(field):
			return getattr(doc, field, None)

		doc.get = mock_get
		return doc

	def test_bmi_calculation_normal(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(height_cm=170, weight_kg=70)
		DiseaseBaselineAssessment.compute_bmi(doc)
		assert doc.bmi == 24.2

	def test_bmi_calculation_obese(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(height_cm=160, weight_kg=100)
		DiseaseBaselineAssessment.compute_bmi(doc)
		assert doc.bmi == 39.1

	def test_bmi_zero_when_missing_height(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(height_cm=0, weight_kg=70)
		DiseaseBaselineAssessment.compute_bmi(doc)
		assert doc.bmi == 0

	def test_bmi_zero_when_missing_weight(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(height_cm=170, weight_kg=0)
		DiseaseBaselineAssessment.compute_bmi(doc)
		assert doc.bmi == 0


class TestBaselineObesityClass:
	"""Test obesity classification derivation."""

	def _make_doc(self, bmi):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = MagicMock(spec=DiseaseBaselineAssessment)
		doc.bmi = bmi
		doc.obesity_class = ""
		return doc

	def test_normal_weight(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(22.0)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == "Normal"

	def test_overweight(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(27.5)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == "Overweight"

	def test_class_i(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(32.0)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == "Class I Obesity"

	def test_class_ii(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(37.0)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == "Class II Obesity"

	def test_class_iii(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(42.0)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == "Class III Obesity"

	def test_zero_bmi(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		doc = self._make_doc(0)
		DiseaseBaselineAssessment.derive_obesity_class(doc)
		assert doc.obesity_class == ""


class TestDataCompleteness:
	"""Test data completeness percentage calculation."""

	def test_empty_baseline_zero_pct(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
			_CLINICAL_FIELDS,
		)
		doc = MagicMock(spec=DiseaseBaselineAssessment)
		doc.data_completeness_pct = 0
		doc.get = MagicMock(return_value=None)

		DiseaseBaselineAssessment.compute_data_completeness(doc)
		assert doc.data_completeness_pct == 0

	def test_full_baseline_100_pct(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
			_CLINICAL_FIELDS,
		)
		doc = MagicMock(spec=DiseaseBaselineAssessment)
		doc.data_completeness_pct = 0
		doc.get = MagicMock(return_value=42)

		DiseaseBaselineAssessment.compute_data_completeness(doc)
		assert doc.data_completeness_pct == 100.0

	def test_partial_completeness(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
			_CLINICAL_FIELDS,
		)
		total = len(_CLINICAL_FIELDS)
		half = total // 2
		values = [42] * half + [None] * (total - half)

		doc = MagicMock(spec=DiseaseBaselineAssessment)
		doc.data_completeness_pct = 0
		doc.get = MagicMock(side_effect=values)

		DiseaseBaselineAssessment.compute_data_completeness(doc)
		expected = round((half / total) * 100, 1)
		assert doc.data_completeness_pct == expected


# ---------------------------------------------------------------------------
# BaselineService tests
# ---------------------------------------------------------------------------

class TestBaselineServiceCreate:
	"""Test baseline creation via the service."""

	@patch("chronic_disease_management.services.baseline.BaselineService.identify_care_gaps")
	@patch("chronic_disease_management.services.baseline.BaselineService.prefill_from_healthcare_data")
	@patch("chronic_disease_management.services.baseline.frappe")
	def test_create_baseline(self, mock_frappe, mock_prefill, mock_gaps):
		from chronic_disease_management.services.baseline import BaselineService

		mock_enrollment = MagicMock()
		mock_enrollment.patient = "PAT-001"
		mock_enrollment.patient_name = "Test Patient"
		mock_enrollment.disease_type = DiseaseType.DIABETES
		mock_enrollment.source_encounter = "ENC-001"
		mock_frappe.get_doc.return_value = mock_enrollment
		mock_frappe.db.exists.return_value = None

		mock_doc = MagicMock()
		mock_doc.name = "CDM-BLA-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc
		mock_prefill.return_value = {}
		mock_gaps.return_value = []

		result = BaselineService.create_baseline("CDM-ENR-2026-00001")

		assert result == "CDM-BLA-2026-00001"
		mock_doc.insert.assert_called_once()
		mock_prefill.assert_called_once_with("CDM-BLA-2026-00001")
		mock_gaps.assert_called_once_with("CDM-BLA-2026-00001")

	@patch("chronic_disease_management.services.baseline.frappe")
	def test_create_duplicate_raises(self, mock_frappe):
		from chronic_disease_management.services.baseline import BaselineService

		mock_enrollment = MagicMock()
		mock_frappe.get_doc.return_value = mock_enrollment
		mock_frappe.db.exists.return_value = "CDM-BLA-2026-00001"

		with pytest.raises(frappe.DuplicateEntryError):
			BaselineService.create_baseline("CDM-ENR-2026-00001")


class TestBaselineServicePrefill:
	"""Test prefill logic with mocked adapters."""

	@patch("chronic_disease_management.services.baseline.frappe")
	def test_prefill_vitals(self, mock_frappe):
		from chronic_disease_management.services.baseline import BaselineService

		mock_doc = MagicMock()
		mock_doc.patient = "PAT-001"
		mock_doc.disease_type = "Diabetes"
		mock_frappe.get_doc.return_value = mock_doc

		with patch(
			"chronic_disease_management.adapters.vitals_adapter.get_latest_vitals",
			return_value={
				"name": "VS-001",
				"signs_date": "2026-04-20",
				"height": 175.0,
				"weight": 80.0,
				"bp_systolic": 130,
				"bp_diastolic": 85,
				"pulse": 72,
			},
		):
			result = BaselineService._prefill_vitals(mock_doc)

		assert "height_cm" in result
		assert "weight_kg" in result
		assert "bp_systolic" in result

	@patch("chronic_disease_management.services.baseline.frappe")
	def test_prefill_vitals_empty(self, mock_frappe):
		from chronic_disease_management.services.baseline import BaselineService

		mock_doc = MagicMock()
		mock_doc.patient = "PAT-002"

		with patch(
			"chronic_disease_management.adapters.vitals_adapter.get_latest_vitals",
			return_value=None,
		):
			result = BaselineService._prefill_vitals(mock_doc)

		assert result == {}

	@patch("chronic_disease_management.services.baseline.frappe")
	def test_prefill_medications(self, mock_frappe):
		from chronic_disease_management.services.baseline import BaselineService

		mock_doc = MagicMock()
		mock_doc.patient = "PAT-001"

		with patch(
			"chronic_disease_management.adapters.medication_adapter.get_medication_snapshot",
			return_value=[
				{"medication": "Metformin", "dosage": "500mg BD"},
				{"drug_name": "Glimepiride", "dosage": "2mg OD"},
			],
		):
			result = BaselineService._prefill_medications(mock_doc)

		assert "current_medications" in result
		assert "Metformin" in mock_doc.current_medications


class TestBaselineCareGaps:
	"""Test care gap identification."""

	def test_diabetes_gap_definitions(self):
		from chronic_disease_management.services.baseline import _get_expected_fields_for_disease

		gaps = _get_expected_fields_for_disease(DiseaseType.DIABETES)
		field_names = [g["field"] for g in gaps]
		assert "hba1c" in field_names
		assert "fasting_blood_sugar" in field_names
		assert "bp_systolic" in field_names
		assert "weight_kg" in field_names

	def test_obesity_gap_definitions(self):
		from chronic_disease_management.services.baseline import _get_expected_fields_for_disease

		gaps = _get_expected_fields_for_disease(DiseaseType.OBESITY)
		field_names = [g["field"] for g in gaps]
		assert "waist_circumference_cm" in field_names
		assert "total_cholesterol" in field_names
		assert "lifestyle_readiness" in field_names

	def test_metabolic_includes_both(self):
		from chronic_disease_management.services.baseline import _get_expected_fields_for_disease

		gaps = _get_expected_fields_for_disease(DiseaseType.METABOLIC)
		field_names = [g["field"] for g in gaps]
		assert "hba1c" in field_names
		assert "waist_circumference_cm" in field_names

	def test_prediabetes_gaps(self):
		from chronic_disease_management.services.baseline import _get_expected_fields_for_disease

		gaps = _get_expected_fields_for_disease(DiseaseType.PREDIABETES)
		field_names = [g["field"] for g in gaps]
		assert "fasting_blood_sugar" in field_names
		assert "hba1c" in field_names
		assert "lifestyle_readiness" in field_names


class TestBaselineRefresh:
	"""Test the refresh logic."""

	@patch("chronic_disease_management.services.baseline.BaselineService.identify_care_gaps")
	@patch("chronic_disease_management.services.baseline.BaselineService.prefill_from_healthcare_data")
	@patch("chronic_disease_management.services.baseline.frappe")
	def test_refresh_returns_summary(self, mock_frappe, mock_prefill, mock_gaps):
		from chronic_disease_management.services.baseline import BaselineService

		mock_doc = MagicMock()
		mock_doc.patient = "PAT-001"
		mock_doc.disease_type = "Diabetes"
		mock_frappe.get_doc.return_value = mock_doc
		mock_prefill.return_value = {"height_cm": 170, "weight_kg": 80}
		mock_gaps.return_value = [{"gap_type": "Lab Test", "description": "HbA1c missing"}]

		result = BaselineService.refresh_baseline("CDM-BLA-2026-00001")

		assert "fields_refreshed" in result
		assert result["care_gaps_found"] == 1
		assert result["overwrite_manual"] is False


# ---------------------------------------------------------------------------
# Auto-fetchable field set
# ---------------------------------------------------------------------------

class TestAutoFetchableFields:
	"""Verify the auto-fetchable field definitions."""

	def test_auto_fetchable_contains_vitals(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		fields = DiseaseBaselineAssessment.get_auto_fetchable_fields()
		assert "height_cm" in fields
		assert "weight_kg" in fields
		assert "bp_systolic" in fields

	def test_auto_fetchable_excludes_clinician_fields(self):
		from chronic_disease_management.cdm_enrollment.doctype.disease_baseline_assessment.disease_baseline_assessment import (
			DiseaseBaselineAssessment,
		)
		fields = DiseaseBaselineAssessment.get_auto_fetchable_fields()
		assert "diagnosis_type" not in fields
		assert "complications_summary" not in fields
		assert "cardiovascular_risk" not in fields
		assert "lifestyle_readiness" not in fields
