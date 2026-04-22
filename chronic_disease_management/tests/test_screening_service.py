"""Unit tests for ScreeningService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.services.screening import ScreeningService


class TestScreeningService:
	"""ScreeningService unit tests."""

	@patch("chronic_disease_management.services.screening.frappe")
	def test_create_screening_returns_name(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-SCR-001"
		mock_frappe.new_doc.return_value = mock_doc

		result = ScreeningService.create_screening(
			patient="PAT-001",
			enrollment="CDM-ENR-001",
			screening_type="HbA1c Review",
			due_date="2026-05-01",
		)
		assert result == "CDM-SCR-001"
		mock_doc.insert.assert_called_once()

	@patch("chronic_disease_management.services.screening.frappe")
	def test_get_due_screenings_returns_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		assert ScreeningService.get_due_screenings() == []


class TestCareGapService:
	"""ScreeningService care gap methods tests."""

	@patch("chronic_disease_management.services.screening.frappe")
	def test_create_care_gap_returns_name(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-GAP-001"
		mock_frappe.new_doc.return_value = mock_doc
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		result = ScreeningService.create_care_gap(
			patient="PAT-001",
			enrollment="CDM-ENR-001",
			gap_type="Lab Gap",
			title="Overdue HbA1c",
		)
		assert result == "CDM-GAP-001"

	@patch("chronic_disease_management.services.screening.frappe")
	def test_get_open_care_gaps_returns_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		assert ScreeningService.get_open_care_gaps() == []

	@patch("chronic_disease_management.services.screening.frappe")
	def test_care_gap_summary_returns_zeros_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = ScreeningService.get_care_gap_summary()
		assert result == {"open": 0, "closed": 0, "deferred": 0}
