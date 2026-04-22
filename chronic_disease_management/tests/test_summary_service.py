"""Unit tests for SummaryService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from chronic_disease_management.services.summary import SummaryService


class TestDoctorSummary:
	"""SummaryService.get_doctor_summary unit tests."""

	@patch("chronic_disease_management.services.summary.frappe")
	def test_returns_required_sections(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		mock_frappe.db.get_value.return_value = None
		result = SummaryService.get_doctor_summary("PAT-001")
		assert result["format"] == "doctor"
		assert "demographics" in result
		assert "enrollment" in result
		assert "goals" in result
		assert "latest_vitals" in result
		assert "medications" in result
		assert "care_gaps" in result
		assert "alerts" in result


class TestPatientSummary:
	"""SummaryService.get_patient_summary unit tests."""

	@patch("chronic_disease_management.services.summary.frappe")
	def test_returns_required_sections(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		mock_frappe.db.get_value.return_value = None
		result = SummaryService.get_patient_summary("PAT-001")
		assert result["format"] == "patient"
		assert "program_info" in result
		assert "my_goals" in result
		assert "my_readings" in result
		assert "upcoming_actions" in result
		assert "my_team" in result
