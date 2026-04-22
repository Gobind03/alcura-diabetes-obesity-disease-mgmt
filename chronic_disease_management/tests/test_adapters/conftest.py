"""Shared fixtures for adapter tests.

Adapter tests mock frappe.db and frappe.get_doc to avoid needing a live site.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_frappe():
	"""Provide a fully mocked frappe module for adapter tests."""
	with patch.dict("sys.modules", {"frappe": MagicMock(), "frappe.utils": MagicMock()}):
		import frappe

		frappe.db = MagicMock()
		frappe.get_doc = MagicMock()
		frappe.get_all = MagicMock(return_value=[])
		frappe.get_meta = MagicMock()
		frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
		frappe.throw = MagicMock(side_effect=Exception("frappe.throw called"))
		frappe.utils.nowdate = MagicMock(return_value="2026-04-22")
		yield frappe


SAMPLE_PATIENT = {
	"name": "PAT-001",
	"patient_name": "John Doe",
	"first_name": "John",
	"last_name": "Doe",
	"sex": "Male",
	"dob": "1985-06-15",
	"blood_group": "O+",
	"status": "Active",
	"mobile": "+1234567890",
	"email": "john@example.com",
	"image": None,
}

SAMPLE_ENCOUNTER = {
	"name": "ENC-001",
	"patient": "PAT-001",
	"patient_name": "John Doe",
	"practitioner": "HP-001",
	"practitioner_name": "Dr. Smith",
	"encounter_date": "2026-04-15",
	"encounter_time": "10:00:00",
	"medical_department": "Endocrinology",
	"status": "Submitted",
	"appointment": "APT-001",
}

SAMPLE_VITALS = {
	"name": "VS-001",
	"patient": "PAT-001",
	"signs_date": "2026-04-15",
	"signs_time": "10:05:00",
	"temperature": 98.6,
	"pulse": 72,
	"respiratory_rate": 16,
	"bp_systolic": 130,
	"bp_diastolic": 85,
	"height": 175,
	"weight": 82,
	"bmi": 26.8,
	"vital_signs_note": "",
}

SAMPLE_LAB = {
	"name": "LT-001",
	"patient": "PAT-001",
	"template": "HbA1c",
	"lab_test_name": "HbA1c",
	"result_date": "2026-04-10",
	"status": "Completed",
	"practitioner": "HP-001",
	"lab_test_comment": "7.2%",
}
