"""Adapter for the Healthcare Practitioner doctype."""

from __future__ import annotations

from typing import Any

import frappe

from alcura_diabetes_obesity_disease_mgmt.adapters.base import (
	doctype_exists,
	require_doctype,
	safe_get_all,
)

_PRACTITIONER_DT = "Healthcare Practitioner"

_PRACTITIONER_FIELDS = [
	"name",
	"practitioner_name",
	"department",
	"designation",
	"mobile_phone",
	"status",
]


def get_practitioner_info(practitioner_id: str) -> dict[str, Any] | None:
	"""Return basic information for a healthcare practitioner.

	Args:
		practitioner_id: Healthcare Practitioner ID.
	"""
	require_doctype(_PRACTITIONER_DT)
	return frappe.db.get_value(
		_PRACTITIONER_DT,
		practitioner_id,
		_PRACTITIONER_FIELDS,
		as_dict=True,
	)


def get_practitioners_for_department(
	department: str,
	limit: int = 50,
) -> list[dict]:
	"""Return active practitioners in a given medical department.

	Args:
		department: Medical Department name.
		limit: Maximum results.
	"""
	return safe_get_all(
		_PRACTITIONER_DT,
		filters={"department": department, "status": "Active"},
		fields=_PRACTITIONER_FIELDS,
		order_by="practitioner_name asc",
		limit_page_length=limit,
	)


def practitioner_exists(practitioner_id: str) -> bool:
	"""Check if a practitioner record exists."""
	if not doctype_exists(_PRACTITIONER_DT):
		return False
	return bool(frappe.db.exists(_PRACTITIONER_DT, practitioner_id))
