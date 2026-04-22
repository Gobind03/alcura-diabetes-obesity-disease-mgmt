"""Care coordinator queue and action services."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate


class CoordinatorService:
	"""Queue membership logic and priority scoring for care coordinators."""

	@staticmethod
	def get_queue(limit: int = 100) -> list[dict[str, Any]]:
		"""Return a prioritized queue of patients needing coordinator attention.

		Combines: overdue reviews, overdue screenings, repeated alerts,
		poor adherence, unresolved care gaps.
		"""
		queue_items: list[dict[str, Any]] = []

		queue_items.extend(CoordinatorService._overdue_visits())
		queue_items.extend(CoordinatorService._overdue_labs())
		queue_items.extend(CoordinatorService._repeated_alerts())
		queue_items.extend(CoordinatorService._unresolved_gaps())

		queue_items.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
		return queue_items[:limit]

	@staticmethod
	def log_action(
		patient: str,
		enrollment: str,
		action_type: str,
		notes: str | None = None,
		related_gap: str | None = None,
		related_alert: str | None = None,
	) -> str:
		"""Log a coordinator action."""
		doc = frappe.new_doc("Care Coordinator Action")
		doc.patient = patient
		doc.enrollment = enrollment
		doc.action_type = action_type
		doc.action_date = nowdate()
		doc.performed_by = frappe.session.user
		if notes:
			doc.notes = notes
		if related_gap:
			doc.related_gap = related_gap
		if related_alert:
			doc.related_alert = related_alert
		doc.insert()
		return doc.name

	@staticmethod
	def get_actions_for_patient(patient: str, limit: int = 20) -> list[dict]:
		"""Return recent coordinator actions for a patient."""
		if not frappe.db.exists("DocType", "Care Coordinator Action"):
			return []

		return frappe.get_all(
			"Care Coordinator Action",
			filters={"patient": patient},
			fields=[
				"name", "action_type", "action_date",
				"performed_by", "notes",
			],
			order_by="action_date desc",
			limit_page_length=limit,
		)

	# ------------------------------------------------------------------
	# Private queue builders
	# ------------------------------------------------------------------

	@staticmethod
	def _overdue_visits() -> list[dict]:
		if not frappe.db.exists("DocType", "Disease Review Sheet"):
			return []

		reviews = frappe.get_all(
			"Disease Review Sheet",
			filters={
				"status": "Scheduled",
				"due_date": ["<", nowdate()],
			},
			fields=["patient", "patient_name", "due_date", "review_type"],
			limit_page_length=50,
		)
		return [
			{
				"patient": r.patient,
				"patient_name": r.patient_name,
				"reason": f"Overdue {r.review_type}",
				"due_date": r.due_date,
				"category": "Overdue Visit",
				"priority_score": 80,
			}
			for r in reviews
		]

	@staticmethod
	def _overdue_labs() -> list[dict]:
		if not frappe.db.exists("DocType", "Complication Screening Tracker"):
			return []

		items = frappe.get_all(
			"Complication Screening Tracker",
			filters={
				"status": ["in", ["Due", "Overdue"]],
				"due_date": ["<", nowdate()],
			},
			fields=["patient", "patient_name", "screening_type", "due_date"],
			limit_page_length=50,
		)
		return [
			{
				"patient": i.patient,
				"patient_name": i.patient_name,
				"reason": f"Overdue {i.screening_type}",
				"due_date": i.due_date,
				"category": "Overdue Lab",
				"priority_score": 70,
			}
			for i in items
		]

	@staticmethod
	def _repeated_alerts() -> list[dict]:
		if not frappe.db.exists("DocType", "CDM Alert"):
			return []

		alerts = frappe.get_all(
			"CDM Alert",
			filters={"status": ["in", ["Open", "Acknowledged"]]},
			fields=["patient", "patient_name", "alert_type", "severity", "count(name) as cnt"],
			group_by="patient, alert_type",
		)
		return [
			{
				"patient": a.patient,
				"patient_name": a.patient_name,
				"reason": f"{a.cnt}x {a.alert_type}",
				"category": "Repeated Alert",
				"priority_score": 90 if a.severity in ("High", "Critical") else 60,
			}
			for a in alerts
			if a.cnt >= 2
		]

	@staticmethod
	def _unresolved_gaps() -> list[dict]:
		if not frappe.db.exists("DocType", "Care Gap"):
			return []

		gaps = frappe.get_all(
			"Care Gap",
			filters={"status": "Open"},
			fields=["patient", "patient_name", "title", "severity"],
			limit_page_length=50,
		)
		return [
			{
				"patient": g.patient,
				"patient_name": g.patient_name,
				"reason": g.title,
				"category": "Unresolved Gap",
				"priority_score": 75 if g.severity == "High" else 50,
			}
			for g in gaps
		]
