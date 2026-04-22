"""Clinical domain constants for reviews, goals, screenings, monitoring, and adherence."""

from enum import StrEnum


class ReviewType(StrEnum):
	INITIAL = "Initial Assessment"
	PERIODIC = "Periodic Review"
	QUARTERLY = "Quarterly Review"
	ANNUAL = "Annual Review"
	URGENT = "Urgent Review"
	DISCHARGE = "Discharge Review"


class GoalType(StrEnum):
	GLYCEMIC = "Glycemic Control"
	WEIGHT = "Weight Management"
	BLOOD_PRESSURE = "Blood Pressure"
	LIPID = "Lipid Management"
	RENAL = "Renal Function"
	LIFESTYLE = "Lifestyle Modification"
	MEDICATION_ADHERENCE = "Medication Adherence"
	DIETARY = "Dietary"
	EXERCISE = "Exercise"
	CUSTOM = "Custom"


GOAL_TYPE_OPTIONS = "\n".join(gt.value for gt in GoalType)


class GoalMetric(StrEnum):
	HBA1C = "HbA1c"
	FASTING_GLUCOSE = "Fasting Glucose"
	POST_PRANDIAL_GLUCOSE = "Post-Prandial Glucose"
	TIR = "TIR"
	WEIGHT = "Weight"
	BMI = "BMI"
	WAIST_CIRCUMFERENCE = "Waist Circumference"
	BP_SYSTOLIC = "BP Systolic"
	BP_DIASTOLIC = "BP Diastolic"
	ACTIVITY_MINUTES = "Activity Minutes/Week"
	DIET_ADHERENCE_SCORE = "Diet Adherence Score"
	CUSTOM = "Custom"


GOAL_METRIC_OPTIONS = "\n".join(gm.value for gm in GoalMetric)


GOAL_METRIC_UNITS: dict[str, str] = {
	GoalMetric.HBA1C: "%",
	GoalMetric.FASTING_GLUCOSE: "mg/dL",
	GoalMetric.POST_PRANDIAL_GLUCOSE: "mg/dL",
	GoalMetric.TIR: "%",
	GoalMetric.WEIGHT: "kg",
	GoalMetric.BMI: "kg/m\u00b2",
	GoalMetric.WAIST_CIRCUMFERENCE: "cm",
	GoalMetric.BP_SYSTOLIC: "mmHg",
	GoalMetric.BP_DIASTOLIC: "mmHg",
	GoalMetric.ACTIVITY_MINUTES: "min/week",
	GoalMetric.DIET_ADHERENCE_SCORE: "%",
}


class CareTeamRole(StrEnum):
	LEAD_PHYSICIAN = "Lead Physician"
	CO_MANAGING_PHYSICIAN = "Co-managing Physician"
	NURSE = "Nurse"
	COORDINATOR = "Coordinator"
	DIETITIAN = "Dietitian"
	OTHER = "Other"


CARE_TEAM_ROLE_OPTIONS = "\n".join(r.value for r in CareTeamRole)


class DiseaseReviewType(StrEnum):
	NEW_EVALUATION = "New Evaluation"
	DIABETES_FOLLOWUP = "Diabetes Follow-up"
	OBESITY_FOLLOWUP = "Obesity Follow-up"
	COMBINED_METABOLIC_FOLLOWUP = "Combined Metabolic Follow-up"
	MEDICATION_TITRATION = "Medication Titration Review"
	LAB_REVIEW = "Lab Review"
	NUTRITION_REVIEW = "Nutrition Review"


DISEASE_REVIEW_TYPE_OPTIONS = "\n".join(rt.value for rt in DiseaseReviewType)


class AppetiteResponse(StrEnum):
	NORMAL = "Normal"
	INCREASED = "Increased"
	DECREASED = "Decreased"
	NO_CHANGE = "No Change"


APPETITE_RESPONSE_OPTIONS = "\n".join(a.value for a in AppetiteResponse)


class SatietyResponse(StrEnum):
	IMPROVED = "Improved"
	WORSENED = "Worsened"
	NO_CHANGE = "No Change"
	NOT_ASSESSED = "Not Assessed"


SATIETY_RESPONSE_OPTIONS = "\n".join(s.value for s in SatietyResponse)


class WeightResponse(StrEnum):
	DECREASED = "Decreased"
	STABLE = "Stable"
	INCREASED = "Increased"
	NOT_MEASURED = "Not Measured"


WEIGHT_RESPONSE_OPTIONS = "\n".join(w.value for w in WeightResponse)


class SideEffectSeverity(StrEnum):
	MILD = "Mild"
	MODERATE = "Moderate"
	SEVERE = "Severe"


SIDE_EFFECT_SEVERITY_OPTIONS = "\n".join(s.value for s in SideEffectSeverity)


class SideEffectAction(StrEnum):
	NONE = "None"
	DOSE_ADJUSTED = "Dose Adjusted"
	MEDICATION_CHANGED = "Medication Changed"
	MEDICATION_STOPPED = "Medication Stopped"
	MONITORING = "Monitoring"


SIDE_EFFECT_ACTION_OPTIONS = "\n".join(a.value for a in SideEffectAction)


class HypoglycemiaSeverity(StrEnum):
	NONE = "None"
	MILD = "Mild"
	MODERATE = "Moderate"
	SEVERE = "Severe"


HYPOGLYCEMIA_SEVERITY_OPTIONS = "\n".join(h.value for h in HypoglycemiaSeverity)


class ScreeningType(StrEnum):
	RETINAL = "Retinal Screening"
	FOOT_EXAM = "Foot Examination"
	RENAL_FUNCTION = "Renal Function Screening"
	CARDIOVASCULAR_RISK = "Cardiovascular Risk Assessment"
	NEUROPATHY = "Neuropathy Screening"
	DENTAL = "Dental Screening"
	MENTAL_HEALTH = "Mental Health Screening"
	SLEEP_APNEA = "Sleep Apnea Screening"


SCREENING_TYPE_OPTIONS = "\n".join(st.value for st in ScreeningType)


class MonitoringEntryType(StrEnum):
	BLOOD_GLUCOSE = "Blood Glucose"
	BLOOD_PRESSURE = "Blood Pressure"
	WEIGHT = "Weight"
	DIETARY_LOG = "Dietary Log"
	EXERCISE_LOG = "Exercise Log"
	MEDICATION_TAKEN = "Medication Taken"
	SYMPTOM_REPORT = "Symptom Report"
	LAB_RESULT = "Lab Result"
	VITAL_SIGNS = "Vital Signs"


MONITORING_ENTRY_TYPE_OPTIONS = "\n".join(met.value for met in MonitoringEntryType)


class AdherenceStatus(StrEnum):
	FULLY_ADHERENT = "Fully Adherent"
	PARTIALLY_ADHERENT = "Partially Adherent"
	NON_ADHERENT = "Non-Adherent"
	NOT_ASSESSED = "Not Assessed"


ADHERENCE_STATUS_OPTIONS = "\n".join(a.value for a in AdherenceStatus)


class CareGapStatus(StrEnum):
	OPEN = "Open"
	IN_PROGRESS = "In Progress"
	CLOSED = "Closed"
	DEFERRED = "Deferred"
	NOT_APPLICABLE = "Not Applicable"


CARE_GAP_STATUS_OPTIONS = "\n".join(cg.value for cg in CareGapStatus)


# Valid state transitions for status machines
ENROLLMENT_STATUS_TRANSITIONS: dict[str, list[str]] = {
	"Draft": ["Active", "Withdrawn"],
	"Active": ["On Hold", "Completed", "Withdrawn"],
	"On Hold": ["Active", "Withdrawn"],
	"Completed": [],
	"Withdrawn": [],
}

CARE_PLAN_STATUS_TRANSITIONS: dict[str, list[str]] = {
	"Draft": ["Active", "Cancelled"],
	"Active": ["Under Review", "Completed", "Cancelled"],
	"Under Review": ["Active", "Completed", "Cancelled"],
	"Completed": [],
	"Cancelled": [],
}

REVIEW_STATUS_TRANSITIONS: dict[str, list[str]] = {
	"Draft": ["In Progress", "Cancelled"],
	"Scheduled": ["In Progress", "Missed", "Rescheduled"],
	"In Progress": ["Completed", "Rescheduled"],
	"Completed": [],
	"Missed": ["Rescheduled"],
	"Rescheduled": ["Scheduled"],
	"Cancelled": [],
}

GOAL_STATUS_TRANSITIONS: dict[str, list[str]] = {
	"Not Started": ["In Progress"],
	"In Progress": ["Achieved", "Partially Met", "Not Met", "Revised"],
	"Achieved": [],
	"Partially Met": ["In Progress", "Revised"],
	"Not Met": ["In Progress", "Revised"],
	"Revised": [],
}
