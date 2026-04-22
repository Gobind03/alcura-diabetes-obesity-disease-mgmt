"""Tests for clinical value formatting utilities."""

from chronic_disease_management.utils.formatters import (
	format_bmi,
	format_bp,
	format_clinical_value,
	format_trend_direction,
)


class TestFormatClinicalValue:
	def test_basic_format(self):
		assert format_clinical_value(7.234, "%", 1) == "7.2 %"

	def test_zero_precision(self):
		assert format_clinical_value(120.6, "mg/dL", 0) == "121 mg/dL"

	def test_no_unit(self):
		assert format_clinical_value(5.5, "", 1) == "5.5"

	def test_none_returns_dash(self):
		assert format_clinical_value(None, "mg/dL") == "--"

	def test_integer_value(self):
		assert format_clinical_value(120, "mmHg", 0) == "120 mmHg"


class TestFormatBP:
	def test_normal_bp(self):
		assert format_bp(120, 80) == "120/80 mmHg"

	def test_float_values_truncated(self):
		assert format_bp(120.7, 80.3) == "120/80 mmHg"

	def test_none_systolic(self):
		assert format_bp(None, 80) == "--"

	def test_none_diastolic(self):
		assert format_bp(120, None) == "--"

	def test_both_none(self):
		assert format_bp(None, None) == "--"


class TestFormatBMI:
	def test_underweight(self):
		result = format_bmi(17.5)
		assert "Underweight" in result

	def test_normal(self):
		result = format_bmi(22.0)
		assert "Normal" in result

	def test_overweight(self):
		result = format_bmi(27.3)
		assert "Overweight" in result
		assert "27.3" in result

	def test_obese_class_1(self):
		result = format_bmi(32.0)
		assert "Obese Class I" in result

	def test_obese_class_2(self):
		result = format_bmi(37.0)
		assert "Obese Class II" in result

	def test_obese_class_3(self):
		result = format_bmi(42.0)
		assert "Obese Class III" in result

	def test_none_returns_dash(self):
		assert format_bmi(None) == "--"


class TestFormatTrendDirection:
	def test_improving_lower_is_better(self):
		assert format_trend_direction(7.0, 8.0, lower_is_better=True) == "Improving"

	def test_worsening_lower_is_better(self):
		assert format_trend_direction(8.0, 7.0, lower_is_better=True) == "Worsening"

	def test_stable(self):
		assert format_trend_direction(7.0, 7.0, lower_is_better=True) == "Stable"

	def test_improving_higher_is_better(self):
		assert format_trend_direction(80, 70, lower_is_better=False) == "Improving"

	def test_worsening_higher_is_better(self):
		assert format_trend_direction(70, 80, lower_is_better=False) == "Worsening"

	def test_none_current(self):
		assert format_trend_direction(None, 7.0) == "--"

	def test_none_previous(self):
		assert format_trend_direction(7.0, None) == "--"

	def test_within_tolerance_is_stable(self):
		assert format_trend_direction(7.005, 7.0, tolerance=0.01) == "Stable"

	def test_outside_tolerance(self):
		assert format_trend_direction(7.02, 7.0, tolerance=0.01) == "Worsening"
