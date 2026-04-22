"""Unit tests for MedicationService."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from chronic_disease_management.services.medication import MedicationService


class TestAdherenceSummary:
	"""MedicationService.get_adherence_summary unit tests."""

	@patch("chronic_disease_management.services.medication.frappe")
	def test_returns_defaults_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = MedicationService.get_adherence_summary("PAT-001")
		assert result["total"] == 0
		assert result["adherence_pct"] is None

	@patch("chronic_disease_management.services.medication.frappe")
	def test_computes_adherence_pct(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"adherence_status": "Taken", "medication_name": "Metformin"},
			{"adherence_status": "Taken", "medication_name": "Metformin"},
			{"adherence_status": "Missed", "medication_name": "Metformin"},
			{"adherence_status": "Taken", "medication_name": "Metformin"},
		]
		result = MedicationService.get_adherence_summary("PAT-001")
		assert result["total"] == 4
		assert result["taken"] == 3
		assert result["missed"] == 1
		assert result["adherence_pct"] == 75.0


class TestTolerability:
	"""MedicationService tolerability tests."""

	@patch("chronic_disease_management.services.medication.frappe")
	def test_returns_defaults_if_doctype_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = MedicationService.get_tolerability_summary("PAT-001")
		assert result["total"] == 0

	@patch("chronic_disease_management.services.medication.frappe")
	def test_returns_active_side_effects_empty_if_missing(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = MedicationService.get_active_side_effects("PAT-001")
		assert result == []
