"""Unit and permission tests for Disease Enrollment doctype and EnrollmentService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest

from alcura_diabetes_obesity_disease_mgmt.constants.disease_types import DiseaseType
from alcura_diabetes_obesity_disease_mgmt.constants.statuses import EnrollmentStatus
from alcura_diabetes_obesity_disease_mgmt.services.enrollment import EnrollmentService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enrollment(
	patient: str = "PAT-0001",
	disease_type: str = DiseaseType.DIABETES,
	status: str = EnrollmentStatus.DRAFT,
	**kwargs,
) -> MagicMock:
	"""Build a mock enrollment doc for unit tests that don't hit the DB."""
	doc = MagicMock()
	doc.patient = patient
	doc.disease_type = disease_type
	doc.program_status = status
	doc.enrollment_date = "2026-04-22"
	doc.name = kwargs.get("name", "CDM-ENR-2026-00001")
	doc.is_new.return_value = kwargs.get("is_new", True)
	for k, v in kwargs.items():
		setattr(doc, k, v)
	return doc


# ---------------------------------------------------------------------------
# Disease type validation
# ---------------------------------------------------------------------------

class TestDiseaseTypeValidation:
	"""Verify that only supported disease types are accepted."""

	def test_valid_types(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_disease_type

		for dt in [DiseaseType.DIABETES, DiseaseType.OBESITY, DiseaseType.METABOLIC, DiseaseType.PREDIABETES]:
			validate_disease_type(dt)

	def test_invalid_type_raises(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_disease_type

		with pytest.raises(frappe.ValidationError):
			validate_disease_type("Imaginary Disease")


# ---------------------------------------------------------------------------
# Status transition validation
# ---------------------------------------------------------------------------

class TestEnrollmentStatusTransitions:
	"""Verify allowed and disallowed status transitions."""

	def test_draft_to_active(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		validate_enrollment_status_transition("Draft", "Active")

	def test_draft_to_withdrawn(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		validate_enrollment_status_transition("Draft", "Withdrawn")

	def test_active_to_on_hold(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		validate_enrollment_status_transition("Active", "On Hold")

	def test_active_to_completed(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		validate_enrollment_status_transition("Active", "Completed")

	def test_on_hold_to_active(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		validate_enrollment_status_transition("On Hold", "Active")

	def test_completed_is_terminal(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		with pytest.raises(frappe.ValidationError):
			validate_enrollment_status_transition("Completed", "Active")

	def test_withdrawn_is_terminal(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		with pytest.raises(frappe.ValidationError):
			validate_enrollment_status_transition("Withdrawn", "Active")

	def test_draft_to_completed_disallowed(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		with pytest.raises(frappe.ValidationError):
			validate_enrollment_status_transition("Draft", "Completed")

	def test_active_to_draft_disallowed(self):
		from alcura_diabetes_obesity_disease_mgmt.utils.validators import validate_enrollment_status_transition

		with pytest.raises(frappe.ValidationError):
			validate_enrollment_status_transition("Active", "Draft")


# ---------------------------------------------------------------------------
# EnrollmentService unit tests (mocked DB)
# ---------------------------------------------------------------------------

class TestEnrollmentServiceEligibility:
	"""Test eligibility checks without a live database."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_eligible_when_no_existing(self, mock_frappe):
		mock_frappe.db.exists.side_effect = lambda *args, **kwargs: (
			True if args == ("DocType", "Disease Enrollment") else None
		)
		mock_frappe._.side_effect = lambda s, *a, **kw: s.format(*a) if a else s

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_eligibility.__wrapped__",
			side_effect=None,
		):
			pass

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.document_helpers.get_enabled_programs",
			return_value=["Diabetes", "Obesity", "Combined Metabolic", "Prediabetes / Metabolic Risk"],
		):
			result = EnrollmentService.check_eligibility("PAT-001", DiseaseType.DIABETES)
			assert result["eligible"] is True

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_ineligible_when_program_disabled(self, mock_frappe):
		mock_frappe._.side_effect = lambda s, *a, **kw: s.format(*a) if a else s

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.document_helpers.get_enabled_programs",
			return_value=["Obesity"],
		):
			result = EnrollmentService.check_eligibility("PAT-001", DiseaseType.DIABETES)
			assert result["eligible"] is False
			assert "not enabled" in result["reason"]


class TestEnrollmentServiceStatusTransitions:
	"""Test service-level status transition methods."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_close_enrollment_calls_update(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.program_status = EnrollmentStatus.ACTIVE
		mock_frappe.get_doc.return_value = mock_doc

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_enrollment_status_transition"
		):
			EnrollmentService.close_enrollment("CDM-ENR-2026-00001", reason="Program goals met")

		mock_doc.save.assert_called_once()
		assert mock_doc.program_status == EnrollmentStatus.COMPLETED

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_suspend_enrollment(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.program_status = EnrollmentStatus.ACTIVE
		mock_frappe.get_doc.return_value = mock_doc

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_enrollment_status_transition"
		):
			EnrollmentService.suspend_enrollment("CDM-ENR-2026-00001", reason="Patient travel")

		assert mock_doc.program_status == EnrollmentStatus.ON_HOLD

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_reactivate_enrollment(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.program_status = EnrollmentStatus.ON_HOLD
		mock_frappe.get_doc.return_value = mock_doc

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_enrollment_status_transition"
		):
			EnrollmentService.reactivate_enrollment("CDM-ENR-2026-00001")

		assert mock_doc.program_status == EnrollmentStatus.ACTIVE

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_withdraw_enrollment(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.program_status = EnrollmentStatus.ACTIVE
		mock_frappe.get_doc.return_value = mock_doc

		with patch(
			"alcura_diabetes_obesity_disease_mgmt.utils.validators.validate_enrollment_status_transition"
		):
			EnrollmentService.withdraw_enrollment("CDM-ENR-2026-00001", reason="Patient request")

		assert mock_doc.program_status == EnrollmentStatus.WITHDRAWN


class TestEnrollmentServiceQueries:
	"""Test query methods with mocked DB."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_get_active_enrollments_returns_list(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-ENR-2026-00001", "disease_type": "Diabetes"},
		]
		result = EnrollmentService.get_active_enrollments("PAT-001")
		assert len(result) == 1

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_get_active_enrollments_empty_when_no_doctype(self, mock_frappe):
		mock_frappe.db.exists.return_value = False
		result = EnrollmentService.get_active_enrollments("PAT-001")
		assert result == []

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_get_active_enrollment_single(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.db.get_value.return_value = {
			"name": "CDM-ENR-2026-00001",
			"disease_type": "Diabetes",
		}
		result = EnrollmentService.get_active_enrollment("PAT-001", "Diabetes")
		assert result is not None

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	def test_check_existing_enrollment(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-ENR-2026-00001", "disease_type": "Diabetes", "program_status": "Active"},
		]
		result = EnrollmentService.check_existing_enrollment("PAT-001")
		assert len(result) == 1


# ---------------------------------------------------------------------------
# Controller validation tests (mocked)
# ---------------------------------------------------------------------------

class TestDiseaseEnrollmentController:
	"""Test controller validation logic in isolation."""

	def test_invalid_disease_type_raises(self):
		from alcura_diabetes_obesity_disease_mgmt.cdm_enrollment.doctype.disease_enrollment.disease_enrollment import (
			DiseaseEnrollment,
		)

		doc = MagicMock(spec=DiseaseEnrollment)
		doc.disease_type = "Not A Real Disease"
		with pytest.raises(frappe.ValidationError):
			DiseaseEnrollment._validate_disease_type(doc)

	def test_future_enrollment_date_raises(self):
		from alcura_diabetes_obesity_disease_mgmt.cdm_enrollment.doctype.disease_enrollment.disease_enrollment import (
			DiseaseEnrollment,
		)

		doc = MagicMock(spec=DiseaseEnrollment)
		doc.enrollment_date = "2099-12-31"
		with pytest.raises(frappe.ValidationError):
			DiseaseEnrollment._validate_enrollment_date(doc)

	def test_valid_enrollment_date_passes(self):
		from alcura_diabetes_obesity_disease_mgmt.cdm_enrollment.doctype.disease_enrollment.disease_enrollment import (
			DiseaseEnrollment,
		)

		doc = MagicMock(spec=DiseaseEnrollment)
		doc.enrollment_date = "2026-01-01"
		DiseaseEnrollment._validate_enrollment_date(doc)


# ---------------------------------------------------------------------------
# OPD context builder (Story 5)
# ---------------------------------------------------------------------------

class TestEnrollmentContextBuilder:
	"""Test the get_enrollment_context helper."""

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_basic_context(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.return_value = {
			"patient_name": "John Doe",
			"sex": "Male",
			"dob": "1980-01-01",
		}
		mock_check.return_value = []

		with patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.date_diff", return_value=16913):
			with patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.nowdate", return_value="2026-04-22"):
				ctx = EnrollmentService.get_enrollment_context("PAT-001")

		assert ctx["patient"] == "PAT-001"
		assert ctx["patient_name"] == "John Doe"
		assert ctx["existing_enrollments"] == []

	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.frappe")
	@patch("alcura_diabetes_obesity_disease_mgmt.services.enrollment.EnrollmentService.check_existing_enrollment")
	def test_encounter_context(self, mock_check, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient_name": "Jane", "sex": "Female", "dob": None},
			{"practitioner": "HP-001", "practitioner_name": "Dr Smith", "medical_department": "General"},
		]
		mock_check.return_value = []

		ctx = EnrollmentService.get_enrollment_context("PAT-002", source_encounter="ENC-001")
		assert ctx["source_encounter"] == "ENC-001"
		assert ctx["practitioner"] == "HP-001"
