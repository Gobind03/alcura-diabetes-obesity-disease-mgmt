"""Unit tests for EncounterContextService and encounter context API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest


# ---------------------------------------------------------------------------
# EncounterContextService tests
# ---------------------------------------------------------------------------

class TestEncounterContextNoEnrollment:

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.frappe")
	def test_returns_no_cdm_data(self, mock_frappe, mock_dt_exists):
		mock_dt_exists.return_value = True
		mock_frappe.db.get_value.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService.get_disease_context("PAT-999")
		assert result["has_cdm_data"] is False


class TestEncounterContextWithEnrollment:

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_pending_review")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._compute_trends")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_care_gaps")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_medications")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_recent_labs")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_recent_vitals")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_active_goals")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_active_care_plan")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService._get_active_enrollment")
	def test_returns_full_context(
		self, mock_enrollment, mock_care_plan, mock_goals,
		mock_vitals, mock_labs, mock_meds, mock_gaps,
		mock_trends, mock_review,
	):
		mock_enrollment.return_value = {
			"name": "CDM-ENR-001",
			"disease_type": "Diabetes",
			"program_status": "Active",
			"enrollment_date": "2026-01-01",
			"practitioner_name": "Dr Smith",
		}
		mock_care_plan.return_value = {
			"name": "CDM-CP-001",
			"status": "Active",
			"start_date": "2026-01-15",
			"review_date": "2026-04-15",
			"practitioner_name": "Dr Smith",
		}
		mock_goals.return_value = [
			{"goal_metric": "HbA1c", "target_value": "< 7%", "current_value": "7.2%", "status": "In Progress", "target_unit": "%"},
		]
		mock_vitals.return_value = {
			"weight": 82.5, "bmi": 27.3,
			"bp_systolic": 130, "bp_diastolic": 85,
			"signs_date": "2026-04-20",
		}
		mock_labs.return_value = {"hba1c": "7.2", "hba1c_date": "2026-04-01"}
		mock_meds.return_value = [{"medication": "Metformin", "status": "Active"}]
		mock_gaps.return_value = [{"description": "Missing foot exam", "status": "Open", "priority": "Medium"}]
		mock_trends.return_value = {"weight_trend": "decreasing", "hba1c_trend": "improving"}
		mock_review.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService.get_disease_context("PAT-001", "ENC-001")

		assert result["has_cdm_data"] is True
		assert result["enrollment"]["name"] == "CDM-ENR-001"
		assert result["care_plan"]["name"] == "CDM-CP-001"
		assert len(result["goals"]) == 1
		assert result["recent_vitals"]["weight"] == 82.5
		assert result["recent_labs"]["hba1c"] == "7.2"
		assert len(result["medications"]) == 1
		assert len(result["care_gaps"]) == 1
		assert result["trends"]["weight_trend"] == "decreasing"


class TestEncounterContextGracefulDegradation:

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	def test_missing_vital_signs_doctype(self, mock_dt_exists):
		mock_dt_exists.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService._get_recent_vitals("PAT-001")
		assert result is None

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	def test_missing_lab_test_doctype(self, mock_dt_exists):
		mock_dt_exists.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService._get_recent_labs("PAT-001")
		assert result is None

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	def test_missing_disease_goal_doctype(self, mock_dt_exists):
		mock_dt_exists.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService._get_active_goals("CDM-CP-001")
		assert result == []

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	def test_missing_review_sheet_doctype(self, mock_dt_exists):
		mock_dt_exists.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		result = EncounterContextService._get_pending_review("PAT-001")
		assert result is None


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------

class TestTrendComputation:

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.frappe")
	def test_weight_decreasing(self, mock_frappe, mock_dt_exists):
		mock_dt_exists.return_value = True
		mock_frappe.get_all.side_effect = [
			[{"weight": 80.0}, {"weight": 85.0}],
			[],  # lab query
		]

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		trends = EncounterContextService._compute_trends("PAT-001")
		assert trends["weight_trend"] == "decreasing"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.frappe")
	def test_weight_increasing(self, mock_frappe, mock_dt_exists):
		mock_dt_exists.return_value = True
		mock_frappe.get_all.side_effect = [
			[{"weight": 90.0}, {"weight": 85.0}],
			[],  # lab query
		]

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		trends = EncounterContextService._compute_trends("PAT-001")
		assert trends["weight_trend"] == "increasing"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.doctype_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.frappe")
	def test_insufficient_data_no_trend(self, mock_frappe, mock_dt_exists):
		mock_dt_exists.return_value = True
		mock_frappe.get_all.side_effect = [
			[{"weight": 80.0}],
			[],
		]

		from alcura_diabetes_obesity_disease_mgmt.services.encounter_context import EncounterContextService
		trends = EncounterContextService._compute_trends("PAT-001")
		assert "weight_trend" not in trends


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestEncounterContextAPI:

	@patch("alcura_diabetes_obesity_disease_mgmt.services.encounter_context.EncounterContextService.get_disease_context")
	def test_get_disease_context_endpoint(self, mock_service):
		mock_service.return_value = {"has_cdm_data": True, "enrollment": {"name": "E1"}}

		from alcura_diabetes_obesity_disease_mgmt.api.encounter_context import get_disease_context
		result = get_disease_context("PAT-001", "ENC-001")
		assert result["has_cdm_data"] is True
		mock_service.assert_called_once_with("PAT-001", encounter="ENC-001")

	@patch("alcura_diabetes_obesity_disease_mgmt.api.encounter_context.frappe")
	def test_get_enrollment_for_patient_found(self, mock_frappe):
		mock_frappe.db.get_value.return_value = "CDM-ENR-001"
		mock_frappe.db.exists.return_value = True

		from alcura_diabetes_obesity_disease_mgmt.api.encounter_context import get_enrollment_for_patient
		result = get_enrollment_for_patient("PAT-001")
		assert result["enrollment"] == "CDM-ENR-001"

	@patch("alcura_diabetes_obesity_disease_mgmt.api.encounter_context.frappe")
	def test_get_enrollment_for_patient_not_found(self, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.api.encounter_context import get_enrollment_for_patient
		result = get_enrollment_for_patient("PAT-999")
		assert result is None
