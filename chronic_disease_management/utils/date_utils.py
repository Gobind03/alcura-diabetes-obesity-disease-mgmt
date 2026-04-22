"""Date calculation utilities for review scheduling and longitudinal trend periods."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import frappe
from frappe.utils import add_days, date_diff, getdate, nowdate

if TYPE_CHECKING:
	pass

PERIOD_TYPES = (
	"last_7_days",
	"last_30_days",
	"last_90_days",
	"last_6_months",
	"last_12_months",
)


def get_review_due_date(
	reference_date: str | datetime.date,
	interval_days: int,
) -> datetime.date:
	"""Calculate the next review due date from a reference date plus interval.

	Args:
		reference_date: The starting date (enrollment date or last review date).
		interval_days: Number of days until next review.

	Returns:
		The computed due date as a ``datetime.date``.
	"""
	ref = getdate(reference_date)
	return getdate(add_days(ref, interval_days))


def get_period_boundaries(
	period_type: str,
	reference_date: str | datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
	"""Return ``(start_date, end_date)`` for a named trend period.

	Args:
		period_type: One of ``PERIOD_TYPES``.
		reference_date: End-anchor date; defaults to today.

	Raises:
		ValueError: If *period_type* is not recognised.
	"""
	end = getdate(reference_date) if reference_date else getdate(nowdate())

	days_map = {
		"last_7_days": 7,
		"last_30_days": 30,
		"last_90_days": 90,
		"last_6_months": 183,
		"last_12_months": 365,
	}
	offset = days_map.get(period_type)
	if offset is None:
		raise ValueError(
			f"Unknown period_type '{period_type}'. Must be one of: {', '.join(PERIOD_TYPES)}"
		)
	start = getdate(add_days(end, -offset))
	return start, end


def days_since(target_date: str | datetime.date) -> int:
	"""Return the number of days elapsed since *target_date* (positive = past)."""
	return date_diff(nowdate(), getdate(target_date))


def days_until(target_date: str | datetime.date) -> int:
	"""Return the number of days remaining until *target_date* (positive = future)."""
	return date_diff(getdate(target_date), nowdate())


def is_overdue(due_date: str | datetime.date, grace_days: int = 0) -> bool:
	"""Check whether *due_date* (plus optional grace period) has passed.

	Returns ``True`` if today is strictly after ``due_date + grace_days``.
	"""
	effective = getdate(add_days(getdate(due_date), grace_days))
	return getdate(nowdate()) > effective
