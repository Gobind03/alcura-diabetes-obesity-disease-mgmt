"""Unit tests for DiabetesService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from chronic_disease_management.services.diabetes import DiabetesService


class TestRecurrentHypoglycemia:
	"""DiabetesService.detect_recurrent_hypoglycemia unit tests."""

	@patch("chronic_disease_management.services.diabetes.frappe")
	def test_returns_not_detected_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = DiabetesService.detect_recurrent_hypoglycemia("PAT-001")
		assert result["detected"] is False
		assert result["count"] == 0

	@patch("chronic_disease_management.services.diabetes.frappe")
	def test_detects_when_threshold_met(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "E1", "numeric_value": 55, "severity": "Mild", "recorded_at": "2026-04-20"},
			{"name": "E2", "numeric_value": 50, "severity": "Moderate", "recorded_at": "2026-04-19"},
			{"name": "E3", "numeric_value": 60, "severity": "Mild", "recorded_at": "2026-04-18"},
		]
		result = DiabetesService.detect_recurrent_hypoglycemia("PAT-001", threshold_count=3)
		assert result["detected"] is True
		assert result["count"] == 3


class TestRepeatedHighFasting:
	"""DiabetesService.detect_repeated_high_fasting unit tests."""

	@patch("chronic_disease_management.services.diabetes.frappe")
	def test_not_detected_below_threshold(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "E1", "numeric_value": 140, "unit": "mg/dL", "recorded_at": "2026-04-20"},
		]
		result = DiabetesService.detect_repeated_high_fasting("PAT-001", threshold_count=3)
		assert result["detected"] is False


class TestDiabetesSummary:
	"""DiabetesService.get_diabetes_summary unit tests."""

	@patch("chronic_disease_management.services.diabetes.frappe")
	def test_returns_no_profile_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = DiabetesService.get_diabetes_summary("CDM-ENR-001")
		assert result["has_profile"] is False
