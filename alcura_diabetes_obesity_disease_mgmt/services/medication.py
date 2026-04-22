"""Medication adherence and side-effect summary services."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


class MedicationService:
	"""Adherence and tolerability analytics across medication logs."""

	@staticmethod
	def get_adherence_summary(
		patient: str,
		enrollment: str | None = None,
		from_date: str | None = None,
		to_date: str | None = None,
	) -> dict[str, Any]:
		"""Compute adherence percentage and breakdown by medication."""
		if not frappe.db.exists("DocType", "Medication Adherence Log"):
			return {"total": 0, "taken": 0, "missed": 0, "delayed": 0, "adherence_pct": None}

		filters: dict[str, Any] = {"patient": patient}
		if enrollment:
			filters["enrollment"] = enrollment
		if from_date and to_date:
			filters["logged_at"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["logged_at"] = [">=", from_date]

		logs = frappe.get_all(
			"Medication Adherence Log",
			filters=filters,
			fields=["adherence_status", "medication_name"],
		)
		total = len(logs)
		taken = sum(1 for l in logs if l.adherence_status == "Taken")
		missed = sum(1 for l in logs if l.adherence_status == "Missed")
		delayed = sum(1 for l in logs if l.adherence_status == "Delayed")

		adherence_pct = round((taken / total) * 100, 1) if total else None

		return {
			"total": total,
			"taken": taken,
			"missed": missed,
			"delayed": delayed,
			"adherence_pct": adherence_pct,
		}

	@staticmethod
	def get_common_missed_reasons(
		patient: str,
		enrollment: str | None = None,
		limit: int = 5,
	) -> list[dict]:
		"""Return the most common reasons for missed/delayed medications."""
		if not frappe.db.exists("DocType", "Medication Adherence Log"):
			return []

		filters: dict[str, Any] = {
			"patient": patient,
			"adherence_status": ["in", ["Missed", "Delayed"]],
			"reason_category": ["is", "set"],
		}
		if enrollment:
			filters["enrollment"] = enrollment

		return frappe.get_all(
			"Medication Adherence Log",
			filters=filters,
			fields=["reason_category", "count(name) as cnt"],
			group_by="reason_category",
			order_by="cnt desc",
			limit_page_length=limit,
		)

	@staticmethod
	def get_active_side_effects(patient: str) -> list[dict]:
		"""Return currently active/ongoing side effects."""
		if not frappe.db.exists("DocType", "Medication Side Effect Log"):
			return []

		return frappe.get_all(
			"Medication Side Effect Log",
			filters={
				"patient": patient,
				"status": ["in", ["Active", "Ongoing"]],
			},
			fields=[
				"name", "medication_name", "effect_name",
				"severity", "onset_date", "status",
			],
			order_by="onset_date desc",
		)

	@staticmethod
	def get_tolerability_summary(
		patient: str,
		enrollment: str | None = None,
	) -> dict[str, Any]:
		"""Medication tolerability overview: side-effect counts by severity."""
		if not frappe.db.exists("DocType", "Medication Side Effect Log"):
			return {"total": 0, "active": 0, "resolved": 0, "by_severity": {}}

		filters: dict[str, Any] = {"patient": patient}
		if enrollment:
			filters["enrollment"] = enrollment

		all_effects = frappe.get_all(
			"Medication Side Effect Log",
			filters=filters,
			fields=["status", "severity"],
		)

		active = sum(1 for e in all_effects if e.status in ("Active", "Ongoing"))
		resolved = sum(1 for e in all_effects if e.status == "Resolved")

		by_severity: dict[str, int] = {}
		for e in all_effects:
			if e.status in ("Active", "Ongoing"):
				by_severity[e.severity] = by_severity.get(e.severity, 0) + 1

		return {
			"total": len(all_effects),
			"active": active,
			"resolved": resolved,
			"by_severity": by_severity,
		}
