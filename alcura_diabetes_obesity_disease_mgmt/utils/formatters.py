"""Formatting utilities for clinical values, dates, and display strings."""

from __future__ import annotations

from frappe.utils import flt


BMI_CATEGORIES = [
	(18.5, "Underweight"),
	(25.0, "Normal"),
	(30.0, "Overweight"),
	(35.0, "Obese Class I"),
	(40.0, "Obese Class II"),
	(float("inf"), "Obese Class III"),
]


def format_clinical_value(value: float | int | None, unit: str = "", precision: int = 1) -> str:
	"""Format a numeric clinical value with unit.

	>>> format_clinical_value(7.234, "%", 1)
	'7.2 %'
	>>> format_clinical_value(None, "mg/dL")
	'--'
	"""
	if value is None:
		return "--"
	rounded = round(flt(value), precision)
	formatted = f"{rounded:.{precision}f}" if precision > 0 else str(int(rounded))
	return f"{formatted} {unit}".strip()


def format_bp(systolic: float | int | None, diastolic: float | int | None) -> str:
	"""Format blood pressure as ``'120/80 mmHg'``.

	>>> format_bp(120, 80)
	'120/80 mmHg'
	>>> format_bp(None, 80)
	'--'
	"""
	if systolic is None or diastolic is None:
		return "--"
	return f"{int(systolic)}/{int(diastolic)} mmHg"


def format_bmi(bmi: float | None) -> str:
	"""Format BMI with a category label.

	>>> format_bmi(27.3)
	'27.3 (Overweight)'
	>>> format_bmi(None)
	'--'
	"""
	if bmi is None:
		return "--"
	bmi_val = flt(bmi, 1)
	category = _bmi_category(bmi_val)
	return f"{bmi_val:.1f} ({category})"


def _bmi_category(bmi: float) -> str:
	for threshold, label in BMI_CATEGORIES:
		if bmi < threshold:
			return label
	return "Obese Class III"


def format_trend_direction(
	current: float | None,
	previous: float | None,
	lower_is_better: bool = True,
	tolerance: float = 0.01,
) -> str:
	"""Classify change between two values as improving/worsening/stable.

	Args:
		current: Most recent value.
		previous: Prior value for comparison.
		lower_is_better: If ``True``, a decrease is "Improving".
		tolerance: Absolute difference below which values are considered stable.

	Returns:
		One of ``"Improving"``, ``"Worsening"``, ``"Stable"``, or ``"--"``.
	"""
	if current is None or previous is None:
		return "--"
	diff = flt(current) - flt(previous)
	if abs(diff) <= tolerance:
		return "Stable"
	if lower_is_better:
		return "Improving" if diff < 0 else "Worsening"
	return "Improving" if diff > 0 else "Worsening"
