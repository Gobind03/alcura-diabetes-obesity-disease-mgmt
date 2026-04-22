"""Tests for document helper utilities (mocked, no live Frappe site required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestSafeGetDoc:
	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_doc_when_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc

		from chronic_disease_management.utils.document_helpers import safe_get_doc
		result = safe_get_doc("Patient", "PAT-001")

		assert result == mock_doc
		mock_frappe.get_doc.assert_called_once_with("Patient", "PAT-001")

	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_none_when_not_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.utils.document_helpers import safe_get_doc
		result = safe_get_doc("Patient", "PAT-MISSING")

		assert result is None
		mock_frappe.get_doc.assert_not_called()

	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_raises_when_not_exists_and_flag_set(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		mock_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
		mock_frappe.throw.side_effect = mock_frappe.DoesNotExistError("not found")

		from chronic_disease_management.utils.document_helpers import safe_get_doc
		with pytest.raises(mock_frappe.DoesNotExistError):
			safe_get_doc("Patient", "PAT-MISSING", raise_on_missing=True)


class TestSafeCreateDoc:
	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_creates_new_doc(self, mock_frappe):
		mock_doc = MagicMock()
		mock_frappe.new_doc.return_value = mock_doc

		from chronic_disease_management.utils.document_helpers import safe_create_doc
		result = safe_create_doc("Patient", {"first_name": "Test"})

		assert result == mock_doc
		mock_doc.update.assert_called_once_with({"first_name": "Test"})
		mock_doc.insert.assert_called_once()

	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_deduplicates_when_existing(self, mock_frappe):
		mock_frappe.db.exists.return_value = "PAT-001"
		existing_doc = MagicMock()
		mock_frappe.get_doc.return_value = existing_doc

		from chronic_disease_management.utils.document_helpers import safe_create_doc
		result = safe_create_doc(
			"Patient",
			{"uid": "12345"},
			deduplicate_field="uid",
		)

		assert result == existing_doc
		mock_frappe.new_doc.assert_not_called()


class TestGetCdmSettings:
	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_cached_doc(self, mock_frappe):
		mock_settings = MagicMock()
		mock_frappe.get_cached_doc.return_value = mock_settings

		from chronic_disease_management.utils.document_helpers import get_cdm_settings
		result = get_cdm_settings()

		assert result == mock_settings
		mock_frappe.get_cached_doc.assert_called_once_with("Disease Management Settings")


class TestPatientLookup:
	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_dict_when_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.return_value = {
			"name": "PAT-001",
			"patient_name": "John Doe",
			"sex": "Male",
			"dob": "1990-01-01",
			"status": "Active",
		}

		from chronic_disease_management.utils.document_helpers import patient_lookup
		result = patient_lookup("PAT-001")

		assert result["patient_name"] == "John Doe"

	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_none_when_not_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.utils.document_helpers import patient_lookup
		result = patient_lookup("PAT-MISSING")

		assert result is None


class TestProgramLookup:
	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_none_when_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.side_effect = lambda dt, name=None: (
			False if dt == "DocType" and name == "Disease Enrollment" else False
		)

		from chronic_disease_management.utils.document_helpers import program_lookup
		result = program_lookup("PAT-001", "Diabetes")

		assert result is None

	@patch("chronic_disease_management.utils.document_helpers.frappe")
	def test_returns_enrollment_when_found(self, mock_frappe):
		mock_frappe.db.exists.side_effect = lambda dt, name=None: True
		mock_frappe.db.get_value.return_value = {
			"name": "ENR-001",
			"disease_type": "Diabetes",
			"status": "Active",
			"enrollment_date": "2026-01-01",
		}

		from chronic_disease_management.utils.document_helpers import program_lookup
		result = program_lookup("PAT-001", "Diabetes")

		assert result["name"] == "ENR-001"
