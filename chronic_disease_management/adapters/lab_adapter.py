"""Adapter for Healthcare Lab Test and Lab Test Template doctypes.

Provides CDM-relevant lab data access: latest results, history, disease-specific
lab lookups, and trend data for longitudinal monitoring.
"""

from __future__ import annotations

from typing import Any

import frappe

from chronic_disease_management.adapters.base import (
	doctype_exists,
	require_doctype,
	safe_get_all,
)
from chronic_disease_management.constants.disease_types import DiseaseType
from chronic_disease_management.constants.lab_markers import (
	DIABETES_MARKERS,
	METABOLIC_MARKERS,
	OBESITY_MARKERS,
)

_LAB_TEST_DT = "Lab Test"
_LAB_TEMPLATE_DT = "Lab Test Template"

_LAB_TEST_FIELDS = [
	"name",
	"patient",
	"template",
	"lab_test_name",
	"result_date",
	"status",
	"practitioner",
	"lab_test_comment",
]


def get_latest_lab_result(
	patient_id: str,
	test_template: str,
) -> dict[str, Any] | None:
	"""Return the most recent lab result for a patient and test template.

	Args:
		patient_id: Patient ID.
		test_template: Lab Test Template name (e.g., ``"HbA1c"``).
	"""
	require_doctype(_LAB_TEST_DT)
	return frappe.db.get_value(
		_LAB_TEST_DT,
		{"patient": patient_id, "template": test_template, "docstatus": 1},
		_LAB_TEST_FIELDS,
		as_dict=True,
		order_by="result_date desc",
	)


def get_lab_history(
	patient_id: str,
	test_template: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
) -> list[dict]:
	"""Return lab test history for a patient, optionally filtered.

	Args:
		patient_id: Patient ID.
		test_template: Optional filter by template.
		from_date: Optional start date.
		to_date: Optional end date.
		limit: Maximum results.
	"""
	filters: dict[str, Any] = {"patient": patient_id, "docstatus": 1}
	if test_template:
		filters["template"] = test_template
	if from_date and to_date:
		filters["result_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["result_date"] = [">=", from_date]
	elif to_date:
		filters["result_date"] = ["<=", to_date]

	return safe_get_all(
		_LAB_TEST_DT,
		filters=filters,
		fields=_LAB_TEST_FIELDS,
		order_by="result_date desc",
		limit_page_length=limit,
	)


def get_relevant_labs(patient_id: str, disease_type: str) -> list[dict]:
	"""Return recent labs relevant to a disease type using marker constants.

	Args:
		patient_id: Patient ID.
		disease_type: One of the supported disease types.

	Returns:
		List of lab result dicts for disease-relevant templates.
	"""
	marker_map = {
		DiseaseType.DIABETES: DIABETES_MARKERS,
		DiseaseType.OBESITY: OBESITY_MARKERS,
		DiseaseType.METABOLIC: METABOLIC_MARKERS,
	}
	markers = marker_map.get(disease_type, [])
	if not markers:
		return []

	return safe_get_all(
		_LAB_TEST_DT,
		filters={
			"patient": patient_id,
			"template": ["in", markers],
			"docstatus": 1,
		},
		fields=_LAB_TEST_FIELDS,
		order_by="result_date desc",
		limit_page_length=100,
	)


def get_lab_trend(
	patient_id: str,
	test_template: str,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	"""Return a time series of lab results for a specific test template.

	Args:
		patient_id: Patient ID.
		test_template: Lab Test Template name.
		from_date: Optional start date.
		to_date: Optional end date.

	Returns:
		List of dicts with ``result_date`` and ``name``, ordered chronologically.
	"""
	filters: dict[str, Any] = {
		"patient": patient_id,
		"template": test_template,
		"docstatus": 1,
	}
	if from_date and to_date:
		filters["result_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["result_date"] = [">=", from_date]
	elif to_date:
		filters["result_date"] = ["<=", to_date]

	return safe_get_all(
		_LAB_TEST_DT,
		filters=filters,
		fields=["name", "result_date", "lab_test_name", "lab_test_comment"],
		order_by="result_date asc",
	)


def check_lab_template_exists(template_name: str) -> bool:
	"""Check if a Lab Test Template exists on this site."""
	if not doctype_exists(_LAB_TEMPLATE_DT):
		return False
	return bool(frappe.db.exists(_LAB_TEMPLATE_DT, template_name))
