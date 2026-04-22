"""Unit tests for LifestyleService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from alcura_diabetes_obesity_disease_mgmt.services.lifestyle import LifestyleService


class TestDietPlanSummary:
	"""LifestyleService.get_diet_plan_summary unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.lifestyle.frappe")
	def test_returns_no_plan_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = LifestyleService.get_diet_plan_summary("CDM-ENR-001")
		assert result["has_plan"] is False


class TestActivitySummary:
	"""LifestyleService.get_activity_summary unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.lifestyle.frappe")
	def test_returns_zeros_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = LifestyleService.get_activity_summary("PAT-001")
		assert result["total_logs"] == 0
		assert result["total_minutes"] == 0


class TestSupplementSummary:
	"""LifestyleService.get_supplement_summary unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.lifestyle.frappe")
	def test_returns_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = LifestyleService.get_supplement_summary("PAT-001")
		assert result == []


class TestLifestyleOverview:
	"""LifestyleService.get_lifestyle_overview unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.lifestyle.frappe")
	def test_returns_all_sections(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = LifestyleService.get_lifestyle_overview("PAT-001", "CDM-ENR-001")
		assert "diet_plan" in result
		assert "meal_adherence" in result
		assert "activity" in result
		assert "supplements" in result
