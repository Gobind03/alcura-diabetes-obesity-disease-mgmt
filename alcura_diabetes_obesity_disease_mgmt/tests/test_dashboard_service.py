"""Unit tests for DashboardService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from alcura_diabetes_obesity_disease_mgmt.services.dashboard import DashboardService


class TestProgramSummary:
	"""DashboardService.get_program_summary unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.dashboard.frappe")
	def test_returns_summary_structure(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = DashboardService.get_program_summary()
		assert "active_enrollments" in result
		assert "by_program" in result
		assert "open_alerts" in result


class TestPatientCockpit:
	"""DashboardService.get_patient_cockpit unit tests."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.dashboard.frappe")
	def test_returns_all_sections(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		mock_frappe.db.get_value.return_value = None
		result = DashboardService.get_patient_cockpit("PAT-001")
		assert "enrollment_summary" in result
		assert "care_plan_summary" in result
		assert "goals_summary" in result
		assert "latest_measurements" in result
		assert "alerts" in result
		assert "care_gaps" in result
