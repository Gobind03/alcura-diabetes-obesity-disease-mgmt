"""Tests for the base adapter compatibility guards."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.adapters.base import CDMDependencyError


class TestDoctypeExists:
	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_true_when_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = True

		from chronic_disease_management.adapters.base import doctype_exists
		doctype_exists.cache_clear()
		assert doctype_exists("Patient") is True

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_false_when_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.adapters.base import doctype_exists
		doctype_exists.cache_clear()
		assert doctype_exists("NonExistent") is False

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_false_on_exception(self, mock_frappe):
		mock_frappe.db.exists.side_effect = Exception("db error")

		from chronic_disease_management.adapters.base import doctype_exists
		doctype_exists.cache_clear()
		assert doctype_exists("Patient") is False


class TestFieldExists:
	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_true_when_field_present(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_meta = MagicMock()
		mock_meta.has_field.return_value = True
		mock_frappe.get_meta.return_value = mock_meta

		from chronic_disease_management.adapters.base import doctype_exists, field_exists
		doctype_exists.cache_clear()
		assert field_exists("Patient", "patient_name") is True

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_false_when_field_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_meta = MagicMock()
		mock_meta.has_field.return_value = False
		mock_frappe.get_meta.return_value = mock_meta

		from chronic_disease_management.adapters.base import doctype_exists, field_exists
		doctype_exists.cache_clear()
		assert field_exists("Patient", "nonexistent_field") is False

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_false_when_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.adapters.base import doctype_exists, field_exists
		doctype_exists.cache_clear()
		assert field_exists("NonExistent", "some_field") is False


class TestRequireDoctype:
	@patch("chronic_disease_management.adapters.base.frappe")
	def test_passes_when_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = True

		from chronic_disease_management.adapters.base import doctype_exists, require_doctype
		doctype_exists.cache_clear()
		require_doctype("Patient")

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_raises_when_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.adapters.base import doctype_exists, require_doctype
		doctype_exists.cache_clear()
		with pytest.raises(CDMDependencyError, match="not installed"):
			require_doctype("NonExistent")


class TestOptionalDoctype:
	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_true_when_exists(self, mock_frappe):
		mock_frappe.db.exists.return_value = True

		from chronic_disease_management.adapters.base import doctype_exists, optional_doctype
		doctype_exists.cache_clear()
		assert optional_doctype("Patient") is True

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_false_when_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.adapters.base import doctype_exists, optional_doctype
		doctype_exists.cache_clear()
		assert optional_doctype("NonExistent") is False


class TestSafeGetAll:
	@patch("chronic_disease_management.adapters.base.frappe")
	def test_returns_empty_when_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.adapters.base import doctype_exists, safe_get_all
		doctype_exists.cache_clear()
		result = safe_get_all("NonExistent", filters={"status": "Active"})
		assert result == []

	@patch("chronic_disease_management.adapters.base.frappe")
	def test_delegates_to_frappe_get_all(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [{"name": "P-001"}]

		from chronic_disease_management.adapters.base import doctype_exists, safe_get_all
		doctype_exists.cache_clear()
		result = safe_get_all("Patient", filters={"status": "Active"}, fields=["name"])
		assert result == [{"name": "P-001"}]


class TestCDMDependencyError:
	def test_error_attributes(self):
		err = CDMDependencyError("test message", doctype="Patient", field="age")
		assert err.doctype == "Patient"
		assert err.field == "age"
		assert "test message" in str(err)
