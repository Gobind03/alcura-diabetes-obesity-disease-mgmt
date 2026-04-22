"""Tests for the patient adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.adapters.base import CDMDependencyError


class TestGetPatientSummary:
	@patch("chronic_disease_management.adapters.patient_adapter.frappe")
	@patch("chronic_disease_management.adapters.patient_adapter.require_doctype")
	def test_returns_patient_data(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"name": "PAT-001",
			"patient_name": "John Doe",
			"sex": "Male",
		}

		from chronic_disease_management.adapters.patient_adapter import get_patient_summary
		result = get_patient_summary("PAT-001")
		assert result["patient_name"] == "John Doe"

	@patch("chronic_disease_management.adapters.patient_adapter.frappe")
	@patch("chronic_disease_management.adapters.patient_adapter.require_doctype")
	def test_throws_when_patient_not_found(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = None
		mock_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
		mock_frappe.throw.side_effect = mock_frappe.DoesNotExistError("not found")

		from chronic_disease_management.adapters.patient_adapter import get_patient_summary
		with pytest.raises(mock_frappe.DoesNotExistError):
			get_patient_summary("PAT-MISSING")


class TestGetPatientRiskFactors:
	@patch("chronic_disease_management.adapters.patient_adapter.frappe")
	@patch("chronic_disease_management.adapters.patient_adapter.require_doctype")
	def test_returns_risk_factors(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"tobacco_current_use": "No",
			"alcohol_current_use": "Occasional",
		}

		from chronic_disease_management.adapters.patient_adapter import get_patient_risk_factors
		result = get_patient_risk_factors("PAT-001")
		assert result["tobacco_current_use"] == "No"

	@patch("chronic_disease_management.adapters.patient_adapter.frappe")
	@patch("chronic_disease_management.adapters.patient_adapter.require_doctype")
	def test_returns_empty_dict_when_none(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from chronic_disease_management.adapters.patient_adapter import get_patient_risk_factors
		result = get_patient_risk_factors("PAT-MISSING")
		assert result == {}


class TestSearchPatients:
	@patch("chronic_disease_management.adapters.patient_adapter.safe_get_all")
	def test_search_with_term(self, mock_get_all):
		mock_get_all.return_value = [{"name": "PAT-001", "patient_name": "John Doe"}]

		from chronic_disease_management.adapters.patient_adapter import search_patients
		result = search_patients(search_term="John")
		assert len(result) == 1

		call_kwargs = mock_get_all.call_args
		filters = call_kwargs[1]["filters"] if "filters" in call_kwargs[1] else call_kwargs[0][1]
		assert "patient_name" in filters

	@patch("chronic_disease_management.adapters.patient_adapter.safe_get_all")
	def test_search_with_filters(self, mock_get_all):
		mock_get_all.return_value = []

		from chronic_disease_management.adapters.patient_adapter import search_patients
		result = search_patients(filters={"status": "Active"})
		assert result == []
