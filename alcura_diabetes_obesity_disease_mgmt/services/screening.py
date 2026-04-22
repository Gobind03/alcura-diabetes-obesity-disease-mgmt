"""Screening and care gap protocol engine service."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, add_days


_SCREENING_DT = "Complication Screening Tracker"
_GAP_DT = "Care Gap"


class ScreeningService:
	"""Protocol engine for screening due/overdue tracking and care gap lifecycle."""

	# ------------------------------------------------------------------
	# Screening tracker
	# ------------------------------------------------------------------

	@staticmethod
	def create_screening(
		patient: str,
		enrollment: str,
		screening_type: str,
		due_date: str,
		care_plan: str | None = None,
	) -> str:
		"""Schedule a screening tracker entry."""
		doc = frappe.new_doc(_SCREENING_DT)
		doc.patient = patient
		doc.enrollment = enrollment
		doc.screening_type = screening_type
		doc.due_date = due_date
		doc.status = "Due"
		if care_plan:
			doc.care_plan = care_plan
		doc.insert()
		return doc.name

	@staticmethod
	def complete_screening(
		screening_id: str,
		result_summary: str | None = None,
		source_encounter: str | None = None,
		source_lab_test: str | None = None,
	) -> None:
		"""Mark a screening as completed."""
		doc = frappe.get_doc(_SCREENING_DT, screening_id)
		doc.status = "Completed"
		doc.completed_date = nowdate()
		if result_summary:
			doc.result_summary = result_summary
		if source_encounter:
			doc.source_encounter = source_encounter
		if source_lab_test:
			doc.source_lab_test = source_lab_test
		doc.save()

	@staticmethod
	def defer_screening(screening_id: str, reason: str) -> None:
		"""Defer a screening with a rationale."""
		doc = frappe.get_doc(_SCREENING_DT, screening_id)
		doc.status = "Deferred"
		doc.deferred_reason = reason
		doc.save()

	@staticmethod
	def evaluate_overdue(enrollment: str | None = None) -> int:
		"""Mark all past-due screenings as Overdue. Returns count updated."""
		if not frappe.db.exists("DocType", _SCREENING_DT):
			return 0

		filters: dict[str, Any] = {
			"status": "Due",
			"due_date": ["<", nowdate()],
		}
		if enrollment:
			filters["enrollment"] = enrollment

		due_items = frappe.get_all(
			_SCREENING_DT,
			filters=filters,
			fields=["name"],
		)
		for item in due_items:
			frappe.db.set_value(_SCREENING_DT, item.name, "status", "Overdue")

		return len(due_items)

	@staticmethod
	def get_due_screenings(
		patient: str | None = None,
		enrollment: str | None = None,
	) -> list[dict]:
		"""Return all Due/Overdue screenings."""
		if not frappe.db.exists("DocType", _SCREENING_DT):
			return []

		filters: dict[str, Any] = {"status": ["in", ["Due", "Overdue"]]}
		if patient:
			filters["patient"] = patient
		if enrollment:
			filters["enrollment"] = enrollment

		return frappe.get_all(
			_SCREENING_DT,
			filters=filters,
			fields=[
				"name", "patient", "patient_name", "screening_type",
				"status", "due_date", "enrollment",
			],
			order_by="due_date asc",
		)

	# ------------------------------------------------------------------
	# Care gap lifecycle
	# ------------------------------------------------------------------

	@staticmethod
	def create_care_gap(
		patient: str,
		enrollment: str,
		gap_type: str,
		title: str,
		severity: str = "Medium",
		due_date: str | None = None,
		evidence_summary: str | None = None,
		linked_screening: str | None = None,
		care_plan: str | None = None,
	) -> str:
		"""Create a care gap entry."""
		doc = frappe.new_doc(_GAP_DT)
		doc.patient = patient
		doc.enrollment = enrollment
		doc.gap_type = gap_type
		doc.title = title
		doc.severity = severity
		doc.status = "Open"
		doc.identified_on = nowdate()
		if due_date:
			doc.due_date = due_date
		if evidence_summary:
			doc.evidence_summary = evidence_summary
		if linked_screening:
			doc.linked_screening_tracker = linked_screening
		if care_plan:
			doc.care_plan = care_plan
		doc.insert()
		return doc.name

	@staticmethod
	def close_care_gap(
		gap_id: str,
		resolution_notes: str | None = None,
	) -> None:
		"""Close a care gap with optional resolution notes."""
		doc = frappe.get_doc(_GAP_DT, gap_id)
		if doc.status == "Closed":
			return
		doc.status = "Closed"
		doc.closed_on = nowdate()
		if resolution_notes:
			doc.resolution_notes = resolution_notes
		doc.save()

	@staticmethod
	def defer_care_gap(gap_id: str, reason: str) -> None:
		"""Defer a care gap."""
		doc = frappe.get_doc(_GAP_DT, gap_id)
		doc.status = "Deferred"
		doc.resolution_notes = reason
		doc.save()

	@staticmethod
	def get_open_care_gaps(
		patient: str | None = None,
		enrollment: str | None = None,
	) -> list[dict]:
		"""Return all open care gaps."""
		if not frappe.db.exists("DocType", _GAP_DT):
			return []

		filters: dict[str, Any] = {"status": "Open"}
		if patient:
			filters["patient"] = patient
		if enrollment:
			filters["enrollment"] = enrollment

		return frappe.get_all(
			_GAP_DT,
			filters=filters,
			fields=[
				"name", "patient", "patient_name", "gap_type", "title",
				"severity", "identified_on", "due_date",
			],
			order_by="severity desc, identified_on asc",
		)

	@staticmethod
	def get_care_gap_summary(enrollment: str | None = None) -> dict[str, int]:
		"""Return counts: open, closed, deferred."""
		if not frappe.db.exists("DocType", _GAP_DT):
			return {"open": 0, "closed": 0, "deferred": 0}

		filters: dict[str, Any] = {}
		if enrollment:
			filters["enrollment"] = enrollment

		gaps = frappe.get_all(_GAP_DT, filters=filters, fields=["status"])
		open_count = sum(1 for g in gaps if g.status == "Open")
		closed = sum(1 for g in gaps if g.status == "Closed")
		deferred = sum(1 for g in gaps if g.status == "Deferred")

		return {"open": open_count, "closed": closed, "deferred": deferred}

	@staticmethod
	def auto_close_gaps_from_screenings(enrollment: str) -> int:
		"""Close care gaps whose linked screening is now completed.

		Returns count of gaps closed.
		"""
		if not frappe.db.exists("DocType", _GAP_DT) or not frappe.db.exists("DocType", _SCREENING_DT):
			return 0

		open_gaps = frappe.get_all(
			_GAP_DT,
			filters={
				"enrollment": enrollment,
				"status": "Open",
				"linked_screening_tracker": ["is", "set"],
			},
			fields=["name", "linked_screening_tracker"],
		)

		closed = 0
		for gap in open_gaps:
			screening_status = frappe.db.get_value(
				_SCREENING_DT, gap.linked_screening_tracker, "status"
			)
			if screening_status == "Completed":
				ScreeningService.close_care_gap(
					gap.name,
					resolution_notes="Auto-closed: linked screening completed.",
				)
				closed += 1

		return closed
