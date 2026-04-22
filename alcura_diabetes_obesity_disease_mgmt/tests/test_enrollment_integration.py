"""Integration tests for OPD-triggered enrollment (Story 5).

Tests enrollment creation from Patient, Patient Encounter, and Patient
Appointment contexts, verifying source linkage and pre-fill correctness.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest

from alcura_diabetes_obesity_disease_mgmt.constants.disease_types import DiseaseType
from alcura_diabetes_obesity_disease_mgmt.constants.statuses import EnrollmentStatus
from alcura_diabetes_obesity_disease_mgmt.services.enrollment import EnrollmentService


# ---------------------------------------------------------------------------
# Context builder tests
# ---------------------------------------------------------------------------

class TestEnrollmentFromPatient:
	"""Enrollment initiated from a Patient record."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_context_from_patient_only(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"patient_name": "Alice Smith",
			"sex": "Female",
			"dob": "1990-06-15",
		}
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context("PAT-001")

		assert ctx["patient"] == "PAT-001"
		assert ctx["patient_name"] == "Alice Smith"
		assert ctx["patient_sex"] == "Female"
		assert "source_encounter" not in ctx
		assert "source_appointment" not in ctx
		assert ctx["existing_enrollments"] == []

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_context_warns_existing(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"patient_name": "Bob Jones",
			"sex": "Male",
			"dob": None,
		}
		mock_check.return_value = [
			{
				"name": "CDM-ENR-2026-00001",
				"disease_type": "Diabetes",
				"program_status": "Active",
			},
		]

		ctx = EnrollmentService.get_enrollment_context("PAT-002")
		assert len(ctx["existing_enrollments"]) == 1
		assert ctx["existing_enrollments"][0]["disease_type"] == "Diabetes"


class TestEnrollmentFromEncounter:
	"""Enrollment initiated from a Patient Encounter."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_encounter_prefills_practitioner(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient_name": "Charlie", "sex": "Male", "dob": None},
			{"practitioner": "HP-001", "practitioner_name": "Dr. Singh", "medical_department": "Endocrinology"},
		]
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context(
			"PAT-003", source_encounter="ENC-100"
		)

		assert ctx["source_encounter"] == "ENC-100"
		assert ctx["practitioner"] == "HP-001"
		assert ctx["practitioner_name"] == "Dr. Singh"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_source_encounter_preserved_in_context(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient_name": "Dana", "sex": "Female", "dob": None},
			{"practitioner": "HP-002", "practitioner_name": "Dr. Patel", "medical_department": "General"},
		]
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context(
			"PAT-004", source_encounter="ENC-200"
		)
		assert ctx.get("source_encounter") == "ENC-200"


class TestEnrollmentFromAppointment:
	"""Enrollment initiated from a Patient Appointment."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_appointment_prefills_practitioner(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient_name": "Eve", "sex": "Female", "dob": None},
			{"practitioner": "HP-003", "practitioner_name": "Dr. Khan", "department": "Internal Medicine"},
		]
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context(
			"PAT-005", source_appointment="APP-100"
		)

		assert ctx["source_appointment"] == "APP-100"
		assert ctx["practitioner"] == "HP-003"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_encounter_takes_priority_over_appointment(self, mock_check, mock_frappe):
		"""When both encounter and appointment are provided, encounter practitioner wins."""
		mock_frappe.db.get_value.side_effect = [
			{"patient_name": "Frank", "sex": "Male", "dob": None},
			{"practitioner": "HP-ENC", "practitioner_name": "Dr. Encounter", "medical_department": "General"},
			{"practitioner": "HP-APT", "practitioner_name": "Dr. Appointment", "department": "General"},
		]
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context(
			"PAT-006",
			source_encounter="ENC-300",
			source_appointment="APP-200",
		)

		assert ctx["practitioner"] == "HP-ENC"
		assert ctx["source_encounter"] == "ENC-300"
		assert ctx["source_appointment"] == "APP-200"


# ---------------------------------------------------------------------------
# Duplicate detection across trigger points
# ---------------------------------------------------------------------------

class TestDuplicateDetectionAcrossTriggers:
	"""Verify duplicate detection works regardless of enrollment source."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_check_existing_returns_non_terminal(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-ENR-2026-00001", "disease_type": "Diabetes", "program_status": "Active"},
			{"name": "CDM-ENR-2026-00002", "disease_type": "Obesity", "program_status": "Draft"},
		]

		result = EnrollmentService.check_existing_enrollment("PAT-010")
		assert len(result) == 2

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_check_existing_filters_by_type(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-ENR-2026-00001", "disease_type": "Diabetes", "program_status": "Active"},
		]

		result = EnrollmentService.check_existing_enrollment("PAT-010", "Diabetes")
		assert len(result) == 1

		call_args = mock_frappe.get_all.call_args
		assert call_args[1]["filters"]["disease_type"] == "Diabetes"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_check_existing_empty_when_no_doctype(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		result = EnrollmentService.check_existing_enrollment("PAT-010")
		assert result == []


# ---------------------------------------------------------------------------
# Service create_enrollment with source linkage
# ---------------------------------------------------------------------------

class TestCreateEnrollmentWithSource:
	"""Test that create_enrollment properly stores source context."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_patient_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_disease_type")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_eligibility")
	def test_create_with_encounter_source(
		self, mock_elig, mock_vdt, mock_vpe, mock_frappe
	):
		mock_elig.return_value = {"eligible": True, "reason": ""}
		mock_frappe.utils.nowdate.return_value = "2026-04-22"
		mock_doc = MagicMock()
		mock_doc.name = "CDM-ENR-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc

		result = EnrollmentService.create_enrollment(
			patient="PAT-001",
			disease_type=DiseaseType.DIABETES,
			practitioner="HP-001",
			source_encounter="ENC-500",
		)

		assert mock_doc.source_encounter == "ENC-500"
		assert result == "CDM-ENR-2026-00001"

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_patient_exists")
	@patch("alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_disease_type")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_eligibility")
	def test_create_with_appointment_source(
		self, mock_elig, mock_vdt, mock_vpe, mock_frappe
	):
		mock_elig.return_value = {"eligible": True, "reason": ""}
		mock_frappe.utils.nowdate.return_value = "2026-04-22"
		mock_doc = MagicMock()
		mock_doc.name = "CDM-ENR-2026-00002"
		mock_frappe.new_doc.return_value = mock_doc

		result = EnrollmentService.create_enrollment(
			patient="PAT-002",
			disease_type=DiseaseType.OBESITY,
			source_appointment="APP-300",
		)

		assert mock_doc.source_appointment == "APP-300"
		assert result == "CDM-ENR-2026-00002"
