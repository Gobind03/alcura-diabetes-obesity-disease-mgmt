"""Disease type constants used across enrollment, care plans, and protocols."""

from enum import StrEnum


class DiseaseType(StrEnum):
	DIABETES = "Diabetes"
	OBESITY = "Obesity"
	METABOLIC = "Combined Metabolic"
	PREDIABETES = "Prediabetes / Metabolic Risk"


SUPPORTED_DISEASE_TYPES: list[str] = [dt.value for dt in DiseaseType]

DISEASE_TYPE_OPTIONS = "\n".join(SUPPORTED_DISEASE_TYPES)
