"""Unit tests for Disease Review Sheet and ReviewService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
import pytest


# ---------------------------------------------------------------------------
# Review status transition validation
# ---------------------------------------------------------------------------

class TestReviewStatusTransitions:

	def test_draft_to_in_progress(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		validate_review_status_transition("Draft", "In Progress")

	def test_draft_to_cancelled(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		validate_review_status_transition("Draft", "Cancelled")

	def test_scheduled_to_in_progress(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		validate_review_status_transition("Scheduled", "In Progress")

	def test_in_progress_to_completed(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		validate_review_status_transition("In Progress", "Completed")

	def test_completed_is_terminal(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_review_status_transition("Completed", "In Progress")

	def test_missed_to_rescheduled(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		validate_review_status_transition("Missed", "Rescheduled")

	def test_draft_to_completed_disallowed(self):
		from chronic_disease_management.utils.validators import validate_review_status_transition
		with pytest.raises(frappe.ValidationError):
			validate_review_status_transition("Draft", "Completed")


# ---------------------------------------------------------------------------
# ReviewService unit tests
# ---------------------------------------------------------------------------

class TestReviewServiceCreateFromEncounter:

	@patch("chronic_disease_management.services.review.frappe")
	def test_creates_new_review(self, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient": "PAT-001", "practitioner": "HP-001"},
			None,  # no existing draft
			"Diabetes",  # enrollment disease_type
		]
		mock_frappe.db.exists.return_value = True

		mock_doc = MagicMock()
		mock_doc.name = "CDM-RVW-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService.create_review_from_encounter("ENC-001")

		mock_frappe.new_doc.assert_called_once_with("Disease Review Sheet")
		mock_doc.insert.assert_called_once()
		assert result == "CDM-RVW-2026-00001"

	@patch("chronic_disease_management.services.review.frappe")
	def test_returns_existing_draft(self, mock_frappe):
		mock_frappe.db.get_value.side_effect = [
			{"patient": "PAT-001", "practitioner": "HP-001"},
			"CDM-RVW-2026-00099",  # existing draft
		]

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService.create_review_from_encounter("ENC-001")

		mock_frappe.new_doc.assert_not_called()
		assert result == "CDM-RVW-2026-00099"

	@patch("chronic_disease_management.services.review.frappe")
	def test_encounter_not_found_raises(self, mock_frappe):
		mock_frappe.db.get_value.return_value = None
		mock_frappe._.side_effect = lambda s, *a, **kw: s.format(*a) if a else s
		mock_frappe.throw.side_effect = Exception("not found")

		from chronic_disease_management.services.review import ReviewService
		with pytest.raises(Exception, match="not found"):
			ReviewService.create_review_from_encounter("ENC-INVALID")


class TestReviewServiceSchedule:

	@patch("chronic_disease_management.services.review.frappe")
	def test_schedule_review(self, mock_frappe):
		mock_enrollment = MagicMock()
		mock_enrollment.patient = "PAT-001"
		mock_enrollment.disease_type = "Diabetes"
		mock_enrollment.practitioner = "HP-001"
		mock_frappe.get_doc.return_value = mock_enrollment

		mock_doc = MagicMock()
		mock_doc.name = "CDM-RVW-2026-00001"
		mock_frappe.new_doc.return_value = mock_doc

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService.schedule_review(
			"CDM-ENR-2026-00001", "Diabetes Follow-up", "2026-07-01"
		)

		assert mock_doc.status == "Scheduled"
		assert mock_doc.review_type == "Diabetes Follow-up"
		mock_doc.insert.assert_called_once()
		assert result == "CDM-RVW-2026-00001"


class TestReviewServiceQueries:

	@patch("chronic_disease_management.services.review.frappe")
	def test_get_reviews_for_enrollment(self, mock_frappe):
		mock_frappe.db.exists.return_value = True
		mock_frappe.get_all.return_value = [
			{"name": "CDM-RVW-001", "review_type": "Diabetes Follow-up", "status": "Completed"},
		]

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService.get_reviews_for_enrollment("CDM-ENR-001")
		assert len(result) == 1

	@patch("chronic_disease_management.services.review.frappe")
	def test_get_upcoming_reviews_empty_when_no_doctype(self, mock_frappe):
		mock_frappe.db.exists.return_value = False

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService.get_upcoming_reviews(patient="PAT-001")
		assert result == []


class TestReviewServiceInferType:

	@patch("chronic_disease_management.services.review.frappe")
	def test_infer_diabetes_followup(self, mock_frappe):
		mock_frappe.db.get_value.return_value = "Diabetes"

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService._infer_review_type("PAT-001")
		assert result == "Diabetes Follow-up"

	@patch("chronic_disease_management.services.review.frappe")
	def test_infer_no_enrollment(self, mock_frappe):
		mock_frappe.db.get_value.return_value = None

		from chronic_disease_management.services.review import ReviewService
		result = ReviewService._infer_review_type("PAT-001")
		assert result == "New Evaluation"


# ---------------------------------------------------------------------------
# Controller auto-link tests
# ---------------------------------------------------------------------------

class TestReviewSheetAutoLink:

	@patch("chronic_disease_management.cdm_reviews.doctype.disease_review_sheet.disease_review_sheet.frappe")
	def test_auto_links_enrollment(self, mock_frappe):
		from chronic_disease_management.cdm_reviews.doctype.disease_review_sheet.disease_review_sheet import (
			DiseaseReviewSheet,
		)

		mock_frappe.db.get_value.return_value = {"name": "CDM-ENR-001", "disease_type": "Diabetes"}

		doc = MagicMock(spec=DiseaseReviewSheet)
		doc.patient = "PAT-001"
		doc.enrollment = None
		doc.disease_type = None

		DiseaseReviewSheet._auto_link_enrollment(doc)

		assert doc.enrollment == "CDM-ENR-001"
		assert doc.disease_type == "Diabetes"

	def test_skips_if_enrollment_already_set(self):
		from chronic_disease_management.cdm_reviews.doctype.disease_review_sheet.disease_review_sheet import (
			DiseaseReviewSheet,
		)

		doc = MagicMock(spec=DiseaseReviewSheet)
		doc.patient = "PAT-001"
		doc.enrollment = "CDM-ENR-001"

		DiseaseReviewSheet._auto_link_enrollment(doc)
		# Should not modify enrollment since it's already set


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------

class TestReviewSheetPermissions:

	def test_cdm_patient_has_read_only(self):
		import json
		import os

		json_path = os.path.join(
			os.path.dirname(__file__),
			"..",
			"cdm_reviews",
			"doctype",
			"disease_review_sheet",
			"disease_review_sheet.json",
		)
		with open(json_path) as f:
			meta = json.load(f)

		patient_perms = [p for p in meta["permissions"] if p.get("role") == "CDM Patient"]
		assert len(patient_perms) == 1
		perm = patient_perms[0]
		assert perm.get("read") == 1
		assert not perm.get("write")
		assert not perm.get("create")
