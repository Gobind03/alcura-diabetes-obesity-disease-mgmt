"""Unit tests for CDM Care Plan and CarePlanService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest

from chronic_disease_management.constants.statuses import CarePlanStatus


# ---------------------------------------------------------------------------
# Care Plan status transition validation
# ---------------------------------------------------------------------------

class TestCarePlanStatusTransitions:
	"""Verify allowed and disallowed care plan status transitions."""

	def test_draft_to_active(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		validate_care_plan_status_transition("Draft", "Active")

	def test_draft_to_cancelled(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		validate_care_plan_status_transition("Draft", "Cancelled")

	def test_active_to_under_review(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		validate_care_plan_status_transition("Active", "Under Review")

	def test_active_to_completed(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		validate_care_plan_status_transition("Active", "Completed")

	def test_under_review_to_active(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		validate_care_plan_status_transition("Under Review", "Active")

	def test_completed_is_terminal(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_care_plan_status_transition("Completed", "Active")

	def test_cancelled_is_terminal(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_care_plan_status_transition("Cancelled", "Active")

	def test_draft_to_completed_disallowed(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_care_plan_status_transition("Draft", "Completed")

	def test_active_to_draft_disallowed(self):
		from chronic_disease_management.utils.validators import validate_care_plan_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_care_plan_status_transition("Active", "Draft")


# ---------------------------------------------------------------------------
# CarePlanService unit tests
# ---------------------------------------------------------------------------

class TestCarePlanServiceCreatePlan:

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_create_care_plan_basic(self, mock_frappe):
		mock_enrollment = MagicMock()
		mock_enrollment.patient = "PAT-001"
		mock_enrollment.disease_type = "Diabetes"
		mock_enrollment.practitioner = "HP-001"
		mock_frappe.get_doc.return_value = mock_enrollment

		mock_new_doc = MagicMock()
		mock_new_doc.name = "CDM-CP-2026-00001"
		mock_frappe.new_doc.return_value = mock_new_doc

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.create_care_plan("CDM-ENR-2026-00001")

		mock_frappe.new_doc.assert_called_once_with("CDM Care Plan")
		mock_new_doc.insert.assert_called_once()
		assert result == "CDM-CP-2026-00001"

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_create_care_plan_with_practitioner_override(self, mock_frappe):
		mock_enrollment = MagicMock()
		mock_enrollment.patient = "PAT-001"
		mock_enrollment.disease_type = "Diabetes"
		mock_enrollment.practitioner = "HP-001"
		mock_frappe.get_doc.return_value = mock_enrollment

		mock_new_doc = MagicMock()
		mock_new_doc.name = "CDM-CP-2026-00001"
		mock_frappe.new_doc.return_value = mock_new_doc

		from chronic_disease_management.services.care_plan import CarePlanService
		CarePlanService.create_care_plan("CDM-ENR-2026-00001", practitioner="HP-002")

		assert mock_new_doc.practitioner == "HP-002"


class TestCarePlanServiceGoals:

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_add_goal_creates_disease_goal(self, mock_frappe):
		mock_care_plan = MagicMock()
		mock_care_plan.patient = "PAT-001"
		mock_frappe.get_doc.return_value = mock_care_plan

		mock_goal = MagicMock()
		mock_goal.name = "CDM-GL-2026-00001"
		mock_frappe.new_doc.return_value = mock_goal
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.add_goal(
			care_plan_id="CDM-CP-2026-00001",
			goal_type="Glycemic Control",
			goal_metric="HbA1c",
			target_value="< 7%",
			target_unit="%",
		)

		mock_frappe.new_doc.assert_called_once_with("Disease Goal")
		mock_goal.insert.assert_called_once()
		assert result == "CDM-GL-2026-00001"

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_update_goal_progress(self, mock_frappe):
		mock_goal = MagicMock()
		mock_goal.status = "In Progress"
		mock_frappe.get_doc.return_value = mock_goal

		from chronic_disease_management.services.care_plan import CarePlanService
		CarePlanService.update_goal_progress("CDM-GL-2026-00001", "6.8%", "Achieved")

		assert mock_goal.current_value == "6.8%"
		assert mock_goal.status == "Achieved"
		mock_goal.save.assert_called_once()


class TestCarePlanServiceQueries:

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_get_active_care_plan_found(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.return_value = "CDM-CP-2026-00001"
		mock_doc = MagicMock()
		mock_doc.as_dict.return_value = {"name": "CDM-CP-2026-00001", "status": "Active"}
		mock_frappe.get_doc.return_value = mock_doc

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.get_active_care_plan("CDM-ENR-2026-00001")
		assert result is not None
		assert result["status"] == "Active"

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_get_active_care_plan_not_found(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.return_value = None

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.get_active_care_plan("CDM-ENR-2026-99999")
		assert result is None

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_get_active_care_plan_no_doctype(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.get_active_care_plan("CDM-ENR-2026-00001")
		assert result is None

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_get_goals_for_care_plan(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-GL-001", "goal_metric": "HbA1c", "status": "In Progress"},
		]

		from chronic_disease_management.services.care_plan import CarePlanService
		result = CarePlanService.get_goals_for_care_plan("CDM-CP-2026-00001")
		assert len(result) == 1

	@patch("chronic_disease_management.services.care_plan.frappe")
	def test_get_goal_history_builds_chain(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.side_effect = [
			{"name": "GL-003", "goal_type": "Glycemic Control", "goal_metric": "HbA1c",
			 "target_value": "< 6.5%", "current_value": "7.0%", "status": "Revised",
			 "effective_date": "2026-03-01", "version": 2, "supersedes": "GL-002"},
			{"name": "GL-002", "goal_type": "Glycemic Control", "goal_metric": "HbA1c",
			 "target_value": "< 7%", "current_value": "7.5%", "status": "Revised",
			 "effective_date": "2026-01-01", "version": 1, "supersedes": None},
		]

		from chronic_disease_management.services.care_plan import CarePlanService
		history = CarePlanService.get_goal_history("GL-003")
		assert len(history) == 2
		assert history[0]["version"] == 1
		assert history[1]["version"] == 2


# ---------------------------------------------------------------------------
# Controller validation tests
# ---------------------------------------------------------------------------

class TestCDMCarePlanController:

	def test_future_start_date_raises(self):
		from chronic_disease_management.cdm_care_plans.doctype.cdm_care_plan.cdm_care_plan import (
			CDMCarePlan,
		)
		doc = MagicMock(spec=CDMCarePlan)
		doc.start_date = "2099-12-31"
		with pytest.raises(frappe.ValidationError):
			CDMCarePlan._validate_start_date(doc)

	def test_valid_start_date_passes(self):
		from chronic_disease_management.cdm_care_plans.doctype.cdm_care_plan.cdm_care_plan import (
			CDMCarePlan,
		)
		doc = MagicMock(spec=CDMCarePlan)
		doc.start_date = "2026-01-01"
		CDMCarePlan._validate_start_date(doc)


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------

class TestCarePlanPermissions:

	def test_cdm_patient_has_read_only(self):
		"""CDM Patient role should only have read permission in the doctype JSON."""
		import json
		import os

		json_path = os.path.join(
			os.path.dirname(__file__),
			"..",
			"cdm_care_plans",
			"doctype",
			"cdm_care_plan",
			"cdm_care_plan.json",
		)
		with open(json_path) as f:
			meta = json.load(f)

		patient_perms = [p for p in meta["permissions"] if p.get("role") == "CDM Patient"]
		assert len(patient_perms) == 1
		perm = patient_perms[0]
		assert perm.get("read") == 1
		assert not perm.get("write")
		assert not perm.get("create")
		assert not perm.get("delete")
