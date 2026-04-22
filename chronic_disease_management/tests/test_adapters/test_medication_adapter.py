"""Tests for the medication adapter."""

from __future__ import annotations

from unittest.mock import patch


class TestGetCurrentMedications:
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_returns_empty_when_doctype_missing(self, mock_optional):
		mock_optional.return_value = False

		from chronic_disease_management.adapters.medication_adapter import get_current_medications
		result = get_current_medications("PAT-001")
		assert result == []

	@patch("chronic_disease_management.adapters.medication_adapter.safe_get_all")
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_returns_medications_when_available(self, mock_optional, mock_get_all):
		mock_optional.return_value = True
		mock_get_all.return_value = [{"name": "MR-001", "medication": "Metformin"}]

		from chronic_disease_management.adapters.medication_adapter import get_current_medications
		result = get_current_medications("PAT-001")
		assert len(result) == 1


class TestGetMedicationSnapshot:
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_returns_empty_when_no_doctypes(self, mock_optional):
		mock_optional.return_value = False

		from chronic_disease_management.adapters.medication_adapter import get_medication_snapshot
		result = get_medication_snapshot("PAT-001")
		assert result == []

	@patch("chronic_disease_management.adapters.medication_adapter.frappe")
	@patch("chronic_disease_management.adapters.medication_adapter.safe_get_all")
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_combines_medication_requests_and_prescriptions(
		self, mock_optional, mock_get_all, mock_frappe
	):
		mock_optional.return_value = True
		mock_get_all.return_value = [{"name": "MR-001", "medication": "Metformin"}]
		mock_frappe.get_all.side_effect = [
			[{"name": "ENC-001"}],
			[{"drug_name": "Glimepiride", "dosage": "2mg"}],
		]

		from chronic_disease_management.adapters.medication_adapter import get_medication_snapshot
		result = get_medication_snapshot("PAT-001")
		assert len(result) >= 1


class TestGetMedicationHistory:
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_returns_empty_when_doctype_missing(self, mock_optional):
		mock_optional.return_value = False

		from chronic_disease_management.adapters.medication_adapter import get_medication_history
		result = get_medication_history("PAT-001")
		assert result == []

	@patch("chronic_disease_management.adapters.medication_adapter.safe_get_all")
	@patch("chronic_disease_management.adapters.medication_adapter.optional_doctype")
	def test_returns_history_with_date_filters(self, mock_optional, mock_get_all):
		mock_optional.return_value = True
		mock_get_all.return_value = [{"name": "MR-001"}]

		from chronic_disease_management.adapters.medication_adapter import get_medication_history
		result = get_medication_history("PAT-001", from_date="2026-01-01", to_date="2026-04-22")
		assert len(result) == 1
