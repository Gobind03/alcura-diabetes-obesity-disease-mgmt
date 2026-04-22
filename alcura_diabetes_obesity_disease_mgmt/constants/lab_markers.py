"""Lab marker constants for disease-specific monitoring.

These map to Lab Test Template names in the Healthcare module.
Actual template names may vary by site — these provide default references.
"""


class DiabetesMarker:
	HBA1C = "HbA1c"
	FASTING_BLOOD_SUGAR = "Fasting Blood Sugar"
	POST_PRANDIAL_BLOOD_SUGAR = "Post Prandial Blood Sugar"
	RANDOM_BLOOD_SUGAR = "Random Blood Sugar"
	FASTING_INSULIN = "Fasting Insulin"
	C_PEPTIDE = "C-Peptide"
	URINE_MICROALBUMIN = "Urine Microalbumin"
	SERUM_CREATININE = "Serum Creatinine"
	EGFR = "eGFR"


class ObesityMarker:
	BMI = "BMI"
	WAIST_CIRCUMFERENCE = "Waist Circumference"
	BODY_FAT_PERCENTAGE = "Body Fat Percentage"
	LIPID_PROFILE = "Lipid Profile"
	TOTAL_CHOLESTEROL = "Total Cholesterol"
	LDL = "LDL Cholesterol"
	HDL = "HDL Cholesterol"
	TRIGLYCERIDES = "Triglycerides"
	LIVER_FUNCTION = "Liver Function Test"
	THYROID_PROFILE = "Thyroid Profile"


class MetabolicMarker:
	FASTING_BLOOD_SUGAR = DiabetesMarker.FASTING_BLOOD_SUGAR
	HBA1C = DiabetesMarker.HBA1C
	LIPID_PROFILE = ObesityMarker.LIPID_PROFILE
	BMI = ObesityMarker.BMI
	BLOOD_PRESSURE_SYSTOLIC = "Blood Pressure Systolic"
	BLOOD_PRESSURE_DIASTOLIC = "Blood Pressure Diastolic"
	URIC_ACID = "Uric Acid"


DIABETES_MARKERS: list[str] = [
	DiabetesMarker.HBA1C,
	DiabetesMarker.FASTING_BLOOD_SUGAR,
	DiabetesMarker.POST_PRANDIAL_BLOOD_SUGAR,
	DiabetesMarker.FASTING_INSULIN,
	DiabetesMarker.SERUM_CREATININE,
	DiabetesMarker.EGFR,
	DiabetesMarker.URINE_MICROALBUMIN,
]

OBESITY_MARKERS: list[str] = [
	ObesityMarker.BMI,
	ObesityMarker.WAIST_CIRCUMFERENCE,
	ObesityMarker.LIPID_PROFILE,
	ObesityMarker.LIVER_FUNCTION,
	ObesityMarker.THYROID_PROFILE,
]

METABOLIC_MARKERS: list[str] = [
	MetabolicMarker.HBA1C,
	MetabolicMarker.FASTING_BLOOD_SUGAR,
	MetabolicMarker.LIPID_PROFILE,
	MetabolicMarker.BMI,
	MetabolicMarker.BLOOD_PRESSURE_SYSTOLIC,
	MetabolicMarker.BLOOD_PRESSURE_DIASTOLIC,
	MetabolicMarker.URIC_ACID,
]
