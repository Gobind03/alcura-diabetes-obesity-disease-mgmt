"""Unit tests for ObesityService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.services.obesity import ObesityService


class TestWeightChangeFromBaseline:
	"""ObesityService.weight_change_from_baseline unit tests."""

	@patch("chronic_disease_management.services.obesity.frappe")
	def test_returns_none_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = ObesityService.weight_change_from_baseline("CDM-ENR-001")
		assert result["baseline_weight"] is None
		assert result["current_weight"] is None


class TestPercentWeightChange:
	"""ObesityService.percent_weight_change unit tests."""

	def test_calculates_correctly(self):
		assert ObesityService.percent_weight_change(100, 95) == -5.0
		assert ObesityService.percent_weight_change(100, 105) == 5.0

	def test_returns_none_for_zero_baseline(self):
		assert ObesityService.percent_weight_change(0, 90) is None


class TestPlateau:
	"""ObesityService.detect_plateau unit tests."""

	@patch("chronic_disease_management.services.obesity.frappe")
	def test_returns_not_detected_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = ObesityService.detect_plateau("PAT-001")
		assert result["detected"] is False

	@patch("chronic_disease_management.services.obesity.frappe")
	def test_detects_plateau_within_variance(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			MagicMock(numeric_value=95.0),
			MagicMock(numeric_value=95.5),
			MagicMock(numeric_value=95.2),
			MagicMock(numeric_value=95.1),
		]
		result = ObesityService.detect_plateau("PAT-001", variance_threshold_kg=1.0)
		assert result["detected"] is True
		assert result["readings_count"] == 4


class TestObesitySummary:
	"""ObesityService.get_obesity_summary unit tests."""

	@patch("chronic_disease_management.services.obesity.frappe")
	def test_returns_no_profile_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = ObesityService.get_obesity_summary("CDM-ENR-001")
		assert result["has_profile"] is False
