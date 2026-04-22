"""Unit tests for CoordinatorService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.services.coordinator import CoordinatorService


class TestCoordinatorQueue:
	"""CoordinatorService.get_queue unit tests."""

	@patch("chronic_disease_management.services.coordinator.frappe")
	def test_returns_empty_list_if_no_doctypes(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = CoordinatorService.get_queue()
		assert isinstance(result, list)
		assert len(result) == 0


class TestLogAction:
	"""CoordinatorService.log_action unit tests."""

	@patch("chronic_disease_management.services.coordinator.frappe")
	def test_log_action_returns_name(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-CCA-001"
		mock_frappe.new_doc.return_value = mock_doc
		mock_frappe.session.user = "admin@test.com"
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		result = CoordinatorService.log_action(
			patient="PAT-001",
			enrollment="CDM-ENR-001",
			action_type="Contacted",
			notes="Called patient",
		)
		assert result == "CDM-CCA-001"
		mock_doc.insert.assert_called_once()
