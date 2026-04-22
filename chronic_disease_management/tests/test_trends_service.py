"""Unit tests for TrendService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from chronic_disease_management.services.trends import TrendService


class TestTrendSeries:
	"""TrendService.get_trend_series unit tests."""

	@patch("chronic_disease_management.services.trends.frappe")
	def test_returns_empty_data_points_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = TrendService.get_trend_series("PAT-001", "Fasting Glucose")
		assert result["data_points"] == []
		assert result["latest"] is None

	@patch("chronic_disease_management.services.trends.frappe")
	def test_computes_trend_direction(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"recorded_at": "2026-04-20 08:00:00", "numeric_value": 120, "secondary_numeric_value": None},
			{"recorded_at": "2026-04-21 08:00:00", "numeric_value": 130, "secondary_numeric_value": None},
		]
		result = TrendService.get_trend_series("PAT-001", "Fasting Glucose", "30d")
		assert result["trend_direction"] == "Increasing"
		assert result["delta"] == 10.0
		assert result["latest"] == 130


class TestMultipleSeries:
	"""TrendService.get_multiple_series unit tests."""

	@patch("chronic_disease_management.services.trends.frappe")
	def test_returns_dict_with_all_types(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = TrendService.get_multiple_series(
			"PAT-001", ["Fasting Glucose", "Weight"]
		)
		assert "Fasting Glucose" in result
		assert "Weight" in result
