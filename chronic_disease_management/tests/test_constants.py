"""Smoke tests for CDM constants — verifies enums and lists are well-formed."""

from chronic_disease_management.constants.clinical import (
	ADHERENCE_STATUS_OPTIONS,
	CARE_GAP_STATUS_OPTIONS,
	CARE_PLAN_STATUS_TRANSITIONS,
	ENROLLMENT_STATUS_TRANSITIONS,
	GOAL_TYPE_OPTIONS,
	MONITORING_ENTRY_TYPE_OPTIONS,
	REVIEW_STATUS_TRANSITIONS,
	SCREENING_TYPE_OPTIONS,
	AdherenceStatus,
	CareGapStatus,
	GoalType,
	MonitoringEntryType,
	ReviewType,
	ScreeningType,
)
from chronic_disease_management.constants.disease_types import (
	SUPPORTED_DISEASE_TYPES,
	DiseaseType,
)
from chronic_disease_management.constants.lab_markers import (
	DIABETES_MARKERS,
	METABOLIC_MARKERS,
	OBESITY_MARKERS,
)
from chronic_disease_management.constants.roles import ALL_CDM_ROLES, CLINICIAN_ROLES
from chronic_disease_management.constants.statuses import (
	AlertSeverity,
	AlertStatus,
	CarePlanStatus,
	EnrollmentStatus,
	GoalStatus,
	ProtocolStatus,
	ReviewStatus,
)


# ---------------------------------------------------------------------------
# Disease types
# ---------------------------------------------------------------------------

def test_disease_types_defined():
	assert len(SUPPORTED_DISEASE_TYPES) == 3
	assert "Diabetes" in SUPPORTED_DISEASE_TYPES
	assert "Obesity" in SUPPORTED_DISEASE_TYPES
	assert "Combined Metabolic" in SUPPORTED_DISEASE_TYPES


def test_disease_type_enum_values():
	assert DiseaseType.DIABETES == "Diabetes"
	assert DiseaseType.OBESITY == "Obesity"
	assert DiseaseType.METABOLIC == "Combined Metabolic"


# ---------------------------------------------------------------------------
# Enrollment / care plan / review statuses (statuses.py)
# ---------------------------------------------------------------------------

def test_enrollment_statuses():
	assert EnrollmentStatus.DRAFT == "Draft"
	assert EnrollmentStatus.ACTIVE == "Active"
	assert EnrollmentStatus.WITHDRAWN == "Withdrawn"


def test_care_plan_statuses():
	assert CarePlanStatus.DRAFT == "Draft"
	assert CarePlanStatus.UNDER_REVIEW == "Under Review"
	assert CarePlanStatus.CANCELLED == "Cancelled"


def test_review_statuses():
	assert ReviewStatus.SCHEDULED == "Scheduled"
	assert ReviewStatus.MISSED == "Missed"


def test_goal_statuses():
	assert GoalStatus.ACHIEVED == "Achieved"
	assert GoalStatus.NOT_STARTED == "Not Started"


def test_alert_severity():
	assert AlertSeverity.CRITICAL == "Critical"
	assert AlertSeverity.WARNING == "Warning"


def test_alert_status():
	assert AlertStatus.OPEN == "Open"
	assert AlertStatus.RESOLVED == "Resolved"


def test_protocol_status():
	assert ProtocolStatus.ACTIVE == "Active"
	assert ProtocolStatus.DEPRECATED == "Deprecated"


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

def test_roles_not_empty():
	assert len(ALL_CDM_ROLES) >= 5
	assert len(CLINICIAN_ROLES) >= 3


def test_clinician_roles_subset_of_all():
	assert set(CLINICIAN_ROLES).issubset(set(ALL_CDM_ROLES))


# ---------------------------------------------------------------------------
# Lab markers
# ---------------------------------------------------------------------------

def test_lab_markers_not_empty():
	assert len(DIABETES_MARKERS) > 0
	assert len(OBESITY_MARKERS) > 0
	assert len(METABOLIC_MARKERS) > 0


def test_hba1c_in_diabetes_markers():
	assert "HbA1c" in DIABETES_MARKERS


def test_bmi_in_obesity_markers():
	assert "BMI" in OBESITY_MARKERS


# ---------------------------------------------------------------------------
# Clinical constants (clinical.py — new enums)
# ---------------------------------------------------------------------------

def test_review_type_enum():
	assert ReviewType.INITIAL == "Initial Assessment"
	assert ReviewType.PERIODIC == "Periodic Review"
	assert ReviewType.ANNUAL == "Annual Review"
	assert ReviewType.URGENT == "Urgent Review"
	assert ReviewType.DISCHARGE == "Discharge Review"
	assert len(ReviewType) >= 6


def test_goal_type_enum():
	assert GoalType.GLYCEMIC == "Glycemic Control"
	assert GoalType.WEIGHT == "Weight Management"
	assert GoalType.DIETARY == "Dietary"
	assert GoalType.EXERCISE == "Exercise"
	assert GoalType.CUSTOM == "Custom"
	assert len(GoalType) >= 10


def test_screening_type_enum():
	assert ScreeningType.RETINAL == "Retinal Screening"
	assert ScreeningType.FOOT_EXAM == "Foot Examination"
	assert ScreeningType.CARDIOVASCULAR_RISK == "Cardiovascular Risk Assessment"
	assert len(ScreeningType) >= 8


def test_monitoring_entry_type_enum():
	assert MonitoringEntryType.BLOOD_GLUCOSE == "Blood Glucose"
	assert MonitoringEntryType.BLOOD_PRESSURE == "Blood Pressure"
	assert MonitoringEntryType.WEIGHT == "Weight"
	assert MonitoringEntryType.MEDICATION_TAKEN == "Medication Taken"
	assert len(MonitoringEntryType) >= 9


def test_adherence_status_enum():
	assert AdherenceStatus.FULLY_ADHERENT == "Fully Adherent"
	assert AdherenceStatus.NON_ADHERENT == "Non-Adherent"
	assert AdherenceStatus.NOT_ASSESSED == "Not Assessed"
	assert len(AdherenceStatus) == 4


def test_care_gap_status_enum():
	assert CareGapStatus.OPEN == "Open"
	assert CareGapStatus.CLOSED == "Closed"
	assert CareGapStatus.NOT_APPLICABLE == "Not Applicable"
	assert len(CareGapStatus) == 5


# ---------------------------------------------------------------------------
# Options strings (for Select field options)
# ---------------------------------------------------------------------------

def test_goal_type_options_multiline():
	lines = GOAL_TYPE_OPTIONS.split("\n")
	assert len(lines) == len(GoalType)


def test_screening_type_options_multiline():
	lines = SCREENING_TYPE_OPTIONS.split("\n")
	assert len(lines) == len(ScreeningType)


def test_monitoring_entry_type_options_multiline():
	lines = MONITORING_ENTRY_TYPE_OPTIONS.split("\n")
	assert len(lines) == len(MonitoringEntryType)


def test_adherence_status_options_multiline():
	lines = ADHERENCE_STATUS_OPTIONS.split("\n")
	assert len(lines) == len(AdherenceStatus)


def test_care_gap_status_options_multiline():
	lines = CARE_GAP_STATUS_OPTIONS.split("\n")
	assert len(lines) == len(CareGapStatus)


# ---------------------------------------------------------------------------
# State transition maps
# ---------------------------------------------------------------------------

def test_enrollment_transitions_cover_all_statuses():
	for status in EnrollmentStatus:
		assert status.value in ENROLLMENT_STATUS_TRANSITIONS


def test_care_plan_transitions_cover_all_statuses():
	for status in CarePlanStatus:
		assert status.value in CARE_PLAN_STATUS_TRANSITIONS


def test_review_transitions_cover_all_statuses():
	for status in ReviewStatus:
		assert status.value in REVIEW_STATUS_TRANSITIONS


def test_terminal_states_have_no_transitions():
	assert ENROLLMENT_STATUS_TRANSITIONS["Completed"] == []
	assert ENROLLMENT_STATUS_TRANSITIONS["Withdrawn"] == []
	assert CARE_PLAN_STATUS_TRANSITIONS["Completed"] == []
	assert CARE_PLAN_STATUS_TRANSITIONS["Cancelled"] == []
	assert REVIEW_STATUS_TRANSITIONS["Completed"] == []
