"""Tests for the encounter adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGetLatestEncounter:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.require_doctype")
	def test_returns_latest_encounter(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"name": "ENC-001",
			"patient": "PAT-001",
			"encounter_date": "2026-04-15",
		}

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_latest_encounter
		result = get_latest_encounter("PAT-001")
		assert result["name"] == "ENC-001"

	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.require_doctype")
	def test_returns_none_when_no_encounters(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_latest_encounter
		result = get_latest_encounter("PAT-001")
		assert result is None

	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.require_doctype")
	def test_filters_by_practitioner(self, mock_require, mock_frappe):
		mock_frappe.db.get_value.return_value = {"name": "ENC-002"}

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_latest_encounter
		get_latest_encounter("PAT-001", practitioner="HP-001")

		call_args = mock_frappe.db.get_value.call_args
		filters = call_args[0][1]
		assert filters["practitioner"] == "HP-001"


class TestGetEncounterHistory:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.safe_get_all")
	def test_returns_history_list(self, mock_get_all):
		mock_get_all.return_value = [
			{"name": "ENC-001", "encounter_date": "2026-04-15"},
			{"name": "ENC-002", "encounter_date": "2026-03-10"},
		]

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_encounter_history
		result = get_encounter_history("PAT-001")
		assert len(result) == 2

	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.safe_get_all")
	def test_applies_date_filters(self, mock_get_all):
		mock_get_all.return_value = []

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_encounter_history
		get_encounter_history("PAT-001", from_date="2026-01-01", to_date="2026-04-22")

		call_kwargs = mock_get_all.call_args[1]
		assert "between" in str(call_kwargs["filters"]["encounter_date"])


class TestGetEncounterPrescriptions:
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.optional_doctype")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.require_doctype")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.frappe")
	def test_returns_all_prescription_types(self, mock_frappe, mock_require, mock_optional):
		mock_optional.return_value = True
		mock_frappe.get_all.return_value = [{"drug_name": "Metformin"}]

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_encounter_prescriptions
		result = get_encounter_prescriptions("ENC-001")

		assert "drug" in result
		assert "lab" in result
		assert "procedure" in result

	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.optional_doctype")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.require_doctype")
	@patch("alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter.frappe")
	def test_returns_empty_when_child_doctypes_missing(self, mock_frappe, mock_require, mock_optional):
		mock_optional.return_value = False

		from alcura_diabetes_obesity_disease_mgmt.adapters.encounter_adapter import get_encounter_prescriptions
		result = get_encounter_prescriptions("ENC-001")

		assert result["drug"] == []
		assert result["lab"] == []
		assert result["procedure"] == []
