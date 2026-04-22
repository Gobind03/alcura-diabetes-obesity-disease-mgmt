"""Unit tests for MonitoringService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from chronic_disease_management.services.monitoring import MonitoringService


class TestMonitoringServiceCreateEntry:
	"""MonitoringService.create_entry unit tests."""

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_create_entry_returns_name(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-HME-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc
		mock_frappe.utils.now_datetime.return_value = "2026-04-22 10:00:00"

		result = MonitoringService.create_entry(
			patient="PAT-001",
			enrollment="CDM-ENR-2026-00001",
			entry_type="Fasting Glucose",
			numeric_value=120.5,
			unit="mg/dL",
			entry_source="Patient",
			is_patient_entered=True,
		)

		assert result == "CDM-HME-2026-00001"
		mock_frappe.new_doc.assert_called_once_with("Home Monitoring Entry")
		mock_doc.insert.assert_called_once()

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_create_entry_sets_patient_entered_flag(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "CDM-HME-2026-00002"
		mock_frappe.new_doc.return_value = mock_doc
		mock_frappe.utils.now_datetime.return_value = "2026-04-22 10:00:00"

		MonitoringService.create_entry(
			patient="PAT-001",
			enrollment="CDM-ENR-2026-00001",
			entry_type="Weight",
			numeric_value=85.0,
			is_patient_entered=True,
		)

		assert mock_doc.is_patient_entered == 1


class TestMonitoringServiceGetEntries:
	"""MonitoringService.get_entries_by_patient unit tests."""

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_returns_empty_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = MonitoringService.get_entries_by_patient("PAT-001")
		assert result == []

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_returns_entries_list(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "HME-001", "entry_type": "Fasting Glucose", "numeric_value": 120},
		]
		result = MonitoringService.get_entries_by_patient("PAT-001")
		assert len(result) == 1
		assert result[0]["entry_type"] == "Fasting Glucose"


class TestMonitoringServiceSupersede:
	"""MonitoringService.supersede_entry unit tests."""

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_supersede_creates_new_entry(self, mock_frappe):
		original = MagicMock()
		original.status = "Active"
		original.name = "CDM-HME-2026-00001"
		original.patient = "PAT-001"
		original.enrollment = "CDM-ENR-2026-00001"
		original.entry_type = "Fasting Glucose"
		original.numeric_value = 120
		original.secondary_numeric_value = None
		original.entry_source = "Patient"
		original.recorded_at = "2026-04-22 10:00:00"
		original.unit = "mg/dL"
		original.care_plan = None
		original.severity = None
		original.medication_context = None
		original.related_review_sheet = None
		original.is_patient_entered = 1
		original.notes = "original"
		original.get = lambda field: getattr(original, field, None)

		mock_frappe.get_doc.return_value = original

		new_doc = MagicMock()
		new_doc.name = "CDM-HME-2026-00002"
		mock_frappe.new_doc.return_value = new_doc
		mock_frappe.session.user = "Administrator"

		result = MonitoringService.supersede_entry(
			"CDM-HME-2026-00001",
			{"numeric_value": 110},
		)

		assert result == "CDM-HME-2026-00002"
		assert original.status == "Superseded"
		original.save.assert_called_once()
		new_doc.insert.assert_called_once()


class TestMonitoringServiceLatest:
	"""MonitoringService.get_latest_reading unit tests."""

	@patch("chronic_disease_management.services.monitoring.frappe")
	def test_returns_none_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		assert MonitoringService.get_latest_reading("PAT-001", "Weight") is None
