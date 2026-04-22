"""Unit tests for AlertService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.services.alert import AlertService


class TestAlertServiceCRUD:
	"""AlertService create/acknowledge/resolve unit tests."""

	@patch("chronic_disease_management.services.alert.frappe")
	def test_create_alert_returns_name(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-ALT-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		result = AlertService.create_alert(
			patient="PAT-001",
			severity="High",
			alert_type="Repeated High Fasting Glucose",
			message="Test alert",
		)
		assert result == "CDM-ALT-2026-00001"
		mock_doc.insert.assert_called_once()

	@patch("chronic_disease_management.services.alert.frappe")
	def test_acknowledge_alert(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.status = "Open"
		mock_frappe.get_doc.return_value = mock_doc
		mock_frappe.session.user = "test@test.com"
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		AlertService.acknowledge_alert("CDM-ALT-001")
		assert mock_doc.status == "Acknowledged"
		mock_doc.save.assert_called_once()

	@patch("chronic_disease_management.services.alert.frappe")
	def test_resolve_alert(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.status = "Acknowledged"
		mock_frappe.get_doc.return_value = mock_doc
		mock_frappe.session.user = "test@test.com"
		mock_frappe.utils.nowdate.return_value = "2026-04-22"

		AlertService.resolve_alert("CDM-ALT-001", resolution_note="Fixed")
		assert mock_doc.status == "Resolved"
		mock_doc.save.assert_called_once()


class TestAlertServiceQueries:
	"""AlertService query method tests."""

	@patch("chronic_disease_management.services.alert.frappe")
	def test_get_open_alerts_returns_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		assert AlertService.get_open_alerts() == []

	@patch("chronic_disease_management.services.alert.frappe")
	def test_get_alert_counts_returns_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		assert AlertService.get_alert_counts_by_severity() == {}


class TestAlertRuleEngine:
	"""AlertService rule engine tests."""

	@patch("chronic_disease_management.services.alert.frappe")
	def test_evaluate_returns_list(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = AlertService.evaluate_patient_alerts("PAT-001")
		assert isinstance(result, list)
