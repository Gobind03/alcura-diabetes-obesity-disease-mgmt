"""Tests for the vitals adapter."""

from __future__ import annotations

from unittest.mock import patch


class TestGetLatestVitals:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.require_doctype")
	def test_returns_latest_vitals(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"name": "VS-001",
			"bp_systolic": 130,
			"bp_diastolic": 85,
			"weight": 82,
			"bmi": 26.8,
		}

		from alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter import get_latest_vitals
		result = get_latest_vitals("PAT-001")
		assert result["bp_systolic"] == 130
		assert result["bmi"] == 26.8

	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.require_doctype")
	def test_returns_none_when_no_vitals(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter import get_latest_vitals
		result = get_latest_vitals("PAT-001")
		assert result is None


class TestGetVitalsHistory:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.safe_get_all")
	def test_returns_history(self, mock_get_all):
		mock_get_all.return_value = [
			{"name": "VS-001", "signs_date": "2026-04-15"},
			{"name": "VS-002", "signs_date": "2026-03-15"},
		]

		from alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter import get_vitals_history
		result = get_vitals_history("PAT-001")
		assert len(result) == 2


class TestGetVitalsTrend:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.require_doctype")
	def test_returns_trend_data(self, mock_require, mock_frappe):
		mock_frappe.get_all.return_value = [
			{"name": "VS-001", "signs_date": "2026-03-01", "bp_systolic": 140},
			{"name": "VS-002", "signs_date": "2026-04-01", "bp_systolic": 130},
		]

		from alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter import get_vitals_trend
		result = get_vitals_trend("PAT-001", "bp_systolic")
		assert len(result) == 2


class TestGetBmiHistory:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter.require_doctype")
	def test_returns_bmi_records(self, mock_require, mock_frappe):
		mock_frappe.get_all.return_value = [
			{"name": "VS-001", "signs_date": "2026-04-15", "weight": 82, "bmi": 26.8},
		]

		from alcura_diabetes_obesity_disease_mgmt.adapters.vitals_adapter import get_bmi_history
		result = get_bmi_history("PAT-001")
		assert len(result) == 1
		assert result[0]["bmi"] == 26.8
