"""Tests for the lab adapter."""

from __future__ import annotations

from unittest.mock import patch


class TestGetLatestLabResult:
	@patch("chronic_disease_management.adapters.lab_adapter.frappe")
	@patch("chronic_disease_management.adapters.lab_adapter.require_doctype")
	def test_returns_latest_result(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"name": "LT-001",
			"template": "HbA1c",
			"result_date": "2026-04-10",
		}

		from chronic_disease_management.adapters.lab_adapter import get_latest_lab_result
		result = get_latest_lab_result("PAT-001", "HbA1c")
		assert result["template"] == "HbA1c"

	@patch("chronic_disease_management.adapters.lab_adapter.frappe")
	@patch("chronic_disease_management.adapters.lab_adapter.require_doctype")
	def test_returns_none_when_no_results(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from chronic_disease_management.adapters.lab_adapter import get_latest_lab_result
		result = get_latest_lab_result("PAT-001", "HbA1c")
		assert result is None


class TestGetRelevantLabs:
	@patch("chronic_disease_management.adapters.lab_adapter.safe_get_all")
	def test_diabetes_markers(self, mock_get_all):
		mock_get_all.return_value = [{"name": "LT-001", "template": "HbA1c"}]

		from chronic_disease_management.adapters.lab_adapter import get_relevant_labs
		result = get_relevant_labs("PAT-001", "Diabetes")
		assert len(result) == 1

		call_kwargs = mock_get_all.call_args[1]
		assert "HbA1c" in call_kwargs["filters"]["template"][1]

	@patch("chronic_disease_management.adapters.lab_adapter.safe_get_all")
	def test_obesity_markers(self, mock_get_all):
		mock_get_all.return_value = []

		from chronic_disease_management.adapters.lab_adapter import get_relevant_labs
		result = get_relevant_labs("PAT-001", "Obesity")
		assert result == []

		call_kwargs = mock_get_all.call_args[1]
		assert "BMI" in call_kwargs["filters"]["template"][1]

	def test_unknown_disease_returns_empty(self):
		from chronic_disease_management.adapters.lab_adapter import get_relevant_labs
		result = get_relevant_labs("PAT-001", "UnknownDisease")
		assert result == []


class TestCheckLabTemplateExists:
	@patch("chronic_disease_management.adapters.lab_adapter.frappe")
	@patch("chronic_disease_management.adapters.lab_adapter.doctype_exists")
	def test_returns_true_when_template_exists(self, mock_dt_exists, mock_frappe):
		mock_dt_exists.return_value = True
		mock_frappe.db.exists.return_value = True

		from chronic_disease_management.adapters.lab_adapter import check_lab_template_exists
		assert check_lab_template_exists("HbA1c") is True

	@patch("chronic_disease_management.adapters.lab_adapter.doctype_exists")
	def test_returns_false_when_doctype_missing(self, mock_dt_exists):
		mock_dt_exists.return_value = False

		from chronic_disease_management.adapters.lab_adapter import check_lab_template_exists
		assert check_lab_template_exists("HbA1c") is False
