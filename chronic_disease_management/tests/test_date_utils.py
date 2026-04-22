"""Tests for date calculation utilities."""

from __future__ import annotations

import datetime
from unittest.mock import patch

from chronic_disease_management.utils.date_utils import (
	PERIOD_TYPES,
	days_since,
	days_until,
	get_period_boundaries,
	get_review_due_date,
	is_overdue,
)


def _fake_nowdate():
	return "2026-04-22"


class TestGetReviewDueDate:
	def test_basic_calculation(self):
		result = get_review_due_date("2026-01-01", 90)
		assert result == datetime.date(2026, 4, 1)

	def test_zero_interval(self):
		result = get_review_due_date("2026-04-22", 0)
		assert result == datetime.date(2026, 4, 22)

	def test_date_object_input(self):
		result = get_review_due_date(datetime.date(2026, 3, 1), 30)
		assert result == datetime.date(2026, 3, 31)

	def test_year_boundary(self):
		result = get_review_due_date("2026-12-01", 60)
		assert result == datetime.date(2027, 1, 30)


class TestGetPeriodBoundaries:
	def test_last_7_days(self):
		start, end = get_period_boundaries("last_7_days", "2026-04-22")
		assert end == datetime.date(2026, 4, 22)
		assert start == datetime.date(2026, 4, 15)

	def test_last_30_days(self):
		start, end = get_period_boundaries("last_30_days", "2026-04-22")
		assert end == datetime.date(2026, 4, 22)
		assert start == datetime.date(2026, 3, 23)

	def test_last_90_days(self):
		start, end = get_period_boundaries("last_90_days", "2026-04-22")
		assert end == datetime.date(2026, 4, 22)
		assert start == datetime.date(2026, 1, 22)

	def test_invalid_period_raises(self):
		import pytest
		with pytest.raises(ValueError, match="Unknown period_type"):
			get_period_boundaries("last_2_days", "2026-04-22")

	def test_all_period_types_valid(self):
		for pt in PERIOD_TYPES:
			start, end = get_period_boundaries(pt, "2026-04-22")
			assert start < end


class TestDaysSince:
	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_past_date(self):
		assert days_since("2026-04-12") == 10

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_today(self):
		assert days_since("2026-04-22") == 0

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_future_date_negative(self):
		assert days_since("2026-04-25") == -3


class TestDaysUntil:
	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_future_date(self):
		assert days_until("2026-04-30") == 8

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_today(self):
		assert days_until("2026-04-22") == 0

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_past_date_negative(self):
		assert days_until("2026-04-20") == -2


class TestIsOverdue:
	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_past_due_date_is_overdue(self):
		assert is_overdue("2026-04-10") is True

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_today_is_not_overdue(self):
		assert is_overdue("2026-04-22") is False

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_future_is_not_overdue(self):
		assert is_overdue("2026-05-01") is False

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_grace_days_extend_deadline(self):
		assert is_overdue("2026-04-18", grace_days=5) is False
		assert is_overdue("2026-04-18", grace_days=3) is True

	@patch("chronic_disease_management.utils.date_utils.nowdate", _fake_nowdate)
	def test_zero_grace(self):
		assert is_overdue("2026-04-21", grace_days=0) is True
