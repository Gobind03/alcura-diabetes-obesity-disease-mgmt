"""Unit tests for Disease Goal doctype and revision logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest

from chronic_disease_management.constants.statuses import GoalStatus


# ---------------------------------------------------------------------------
# Goal target validation
# ---------------------------------------------------------------------------

class TestGoalTargetValidation:

	def test_no_target_raises(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.target_value = None
		doc.target_range_low = None
		doc.target_range_high = None
		with pytest.raises(frappe.ValidationError):
			DiseaseGoal._validate_target(doc)

	def test_single_target_passes(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.target_value = "< 7%"
		doc.target_range_low = None
		doc.target_range_high = None
		DiseaseGoal._validate_target(doc)

	def test_range_target_passes(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.target_value = None
		doc.target_range_low = 70.0
		doc.target_range_high = 130.0
		DiseaseGoal._validate_target(doc)

	def test_inverted_range_raises(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.target_value = None
		doc.target_range_low = 130.0
		doc.target_range_high = 70.0
		with pytest.raises(frappe.ValidationError):
			DiseaseGoal._validate_target(doc)

	def test_equal_range_raises(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.target_value = None
		doc.target_range_low = 100.0
		doc.target_range_high = 100.0
		with pytest.raises(frappe.ValidationError):
			DiseaseGoal._validate_target(doc)


class TestGoalEffectiveDateValidation:

	def test_future_effective_date_raises(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.effective_date = "2099-12-31"
		with pytest.raises(frappe.ValidationError):
			DiseaseGoal._validate_effective_date(doc)

	def test_past_effective_date_passes(self):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)
		doc = MagicMock(spec=DiseaseGoal)
		doc.effective_date = "2026-01-01"
		DiseaseGoal._validate_effective_date(doc)


# ---------------------------------------------------------------------------
# Goal revision logic
# ---------------------------------------------------------------------------

class TestGoalRevision:

	@patch("chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal.frappe")
	def test_revise_creates_new_goal(self, mock_frappe):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)

		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		doc = MagicMock(spec=DiseaseGoal)
		doc.name = "CDM-GL-2026-00001"
		doc.care_plan = "CDM-CP-2026-00001"
		doc.patient = "PAT-001"
		doc.goal_type = "Glycemic Control"
		doc.goal_metric = "HbA1c"
		doc.target_value = "< 7%"
		doc.target_range_low = None
		doc.target_range_high = None
		doc.target_unit = "%"
		doc.baseline_value = "8.5%"
		doc.current_value = "7.2%"
		doc.rationale = "Standard target"
		doc.review_date = "2026-07-01"
		doc.status = GoalStatus.IN_PROGRESS
		doc.version = 1

		new_doc = MagicMock()
		new_doc.name = "CDM-GL-2026-00002"
		mock_frappe.new_doc.return_value = new_doc

		result = DiseaseGoal.revise_goal(
			doc,
			new_target_value="< 6.5%",
			new_rationale="Patient responding well",
		)

		assert doc.status == GoalStatus.REVISED
		doc.save.assert_called_once()
		mock_frappe.new_doc.assert_called_once_with("Disease Goal")
		new_doc.insert.assert_called_once()
		assert new_doc.version == 2
		assert new_doc.supersedes == "CDM-GL-2026-00001"
		assert new_doc.target_value == "< 6.5%"
		assert result == "CDM-GL-2026-00002"

	@patch("chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal.frappe")
	def test_revise_already_revised_raises(self, mock_frappe):
		from chronic_disease_management.cdm_care_plans.doctype.disease_goal.disease_goal import (
			DiseaseGoal,
		)

		doc = MagicMock(spec=DiseaseGoal)
		doc.status = GoalStatus.REVISED
		mock_frappe.ValidationError = frappe.ValidationError
		mock_frappe._.side_effect = lambda s, *a, **kw: s.format(*a) if a else s
		mock_frappe.throw.side_effect = frappe.ValidationError

		with pytest.raises(frappe.ValidationError):
			DiseaseGoal.revise_goal(doc, new_target_value="< 6.5%")


# ---------------------------------------------------------------------------
# Goal status transitions
# ---------------------------------------------------------------------------

class TestGoalStatusTransitions:

	def test_not_started_to_in_progress(self):
		from chronic_disease_management.constants.clinical import GOAL_STATUS_TRANSITIONS
		assert "In Progress" in GOAL_STATUS_TRANSITIONS["Not Started"]

	def test_in_progress_to_achieved(self):
		from chronic_disease_management.constants.clinical import GOAL_STATUS_TRANSITIONS
		assert "Achieved" in GOAL_STATUS_TRANSITIONS["In Progress"]

	def test_revised_is_terminal(self):
		from chronic_disease_management.constants.clinical import GOAL_STATUS_TRANSITIONS
		assert GOAL_STATUS_TRANSITIONS["Revised"] == []

	def test_achieved_is_terminal(self):
		from chronic_disease_management.constants.clinical import GOAL_STATUS_TRANSITIONS
		assert GOAL_STATUS_TRANSITIONS["Achieved"] == []


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------

class TestGoalPermissions:

	def test_cdm_patient_has_read_only(self):
		import json
		import os

		json_path = os.path.join(
			os.path.dirname(__file__),
			"..",
			"cdm_care_plans",
			"doctype",
			"disease_goal",
			"disease_goal.json",
		)
		with open(json_path) as f:
			meta = json.load(f)

		patient_perms = [p for p in meta["permissions"] if p.get("role") == "CDM Patient"]
		assert len(patient_perms) == 1
		perm = patient_perms[0]
		assert perm.get("read") == 1
		assert not perm.get("write")
		assert not perm.get("create")
