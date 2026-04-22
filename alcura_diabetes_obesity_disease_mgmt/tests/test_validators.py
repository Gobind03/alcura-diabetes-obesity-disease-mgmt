"""Tests for CDM validation helpers."""

from __future__ import annotations

import pytest

from alcura_diabetes_obesity_disease_mgmt.utils.validators import (
	validate_care_plan_status_transition,
	validate_disease_type,
	validate_enrollment_status_transition,
	validate_positive_int,
	validate_review_status_transition,
)


class TestValidateDiseaseType:
	def test_valid_types(self):
		for dt in ("Diabetes", "Obesity", "Combined Metabolic"):
			validate_disease_type(dt)

	def test_invalid_type_raises(self):
		with pytest.raises(Exception, match="Invalid disease type"):
			validate_disease_type("Hypertension")

	def test_empty_string_raises(self):
		with pytest.raises(Exception, match="Invalid disease type"):
			validate_disease_type("")


class TestEnrollmentStatusTransition:
	def test_valid_transitions(self):
		validate_enrollment_status_transition("Draft", "Active")
		validate_enrollment_status_transition("Active", "Completed")
		validate_enrollment_status_transition("Active", "Withdrawn")
		validate_enrollment_status_transition("On Hold", "Active")

	def test_invalid_transition_raises(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_enrollment_status_transition("Draft", "Completed")

	def test_terminal_state_raises(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_enrollment_status_transition("Completed", "Active")

	def test_unknown_status_raises(self):
		with pytest.raises(Exception, match="Unknown"):
			validate_enrollment_status_transition("Nonexistent", "Active")


class TestCarePlanStatusTransition:
	def test_valid_transitions(self):
		validate_care_plan_status_transition("Draft", "Active")
		validate_care_plan_status_transition("Active", "Under Review")
		validate_care_plan_status_transition("Under Review", "Active")
		validate_care_plan_status_transition("Active", "Completed")

	def test_invalid_transition_raises(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_care_plan_status_transition("Draft", "Completed")

	def test_terminal_state_raises(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_care_plan_status_transition("Cancelled", "Active")


class TestReviewStatusTransition:
	def test_valid_transitions(self):
		validate_review_status_transition("Scheduled", "In Progress")
		validate_review_status_transition("In Progress", "Completed")
		validate_review_status_transition("Scheduled", "Missed")
		validate_review_status_transition("Missed", "Rescheduled")

	def test_invalid_transition_raises(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_review_status_transition("Scheduled", "Completed")

	def test_completed_is_terminal(self):
		with pytest.raises(Exception, match="cannot transition"):
			validate_review_status_transition("Completed", "Scheduled")


class TestValidatePositiveInt:
	def test_valid_positive(self):
		validate_positive_int(1, "Test")
		validate_positive_int(100, "Test")

	def test_zero_raises(self):
		with pytest.raises(Exception, match="positive integer"):
			validate_positive_int(0, "Test")

	def test_none_raises(self):
		with pytest.raises(Exception, match="positive integer"):
			validate_positive_int(None, "Test")

	def test_negative_raises(self):
		with pytest.raises(Exception, match="positive integer"):
			validate_positive_int(-1, "Test")
