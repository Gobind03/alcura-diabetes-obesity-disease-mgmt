"""Alert service — generating, routing, resolving clinical and compliance alerts.

Includes configurable rule engine for trend-based, frequency-based, and
missed-event-based alert generation.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


_DT = "CDM Alert"


class AlertService:
	"""Manages clinical and compliance alerts for CDM patients."""

	# ------------------------------------------------------------------
	# CRUD
	# ------------------------------------------------------------------

	@staticmethod
	def create_alert(
		patient: str,
		severity: str,
		alert_type: str,
		message: str,
		enrollment: str | None = None,
		care_plan: str | None = None,
		source_doctype: str | None = None,
		source_name: str | None = None,
		evidence_summary: str | None = None,
	) -> str:
		"""Create a clinical alert.

		Returns:
			The name of the created CDM Alert document.
		"""
		doc = frappe.new_doc(_DT)
		doc.patient = patient
		doc.severity = severity
		doc.alert_type = alert_type
		doc.message = message
		doc.status = "Open"
		doc.identified_on = nowdate()
		if enrollment:
			doc.enrollment = enrollment
		if care_plan:
			doc.care_plan = care_plan
		if source_doctype:
			doc.source_reference_doctype = source_doctype
		if source_name:
			doc.source_reference_name = source_name
		if evidence_summary:
			doc.evidence_summary = evidence_summary
		doc.insert()
		return doc.name

	@staticmethod
	def acknowledge_alert(alert_id: str, user: str | None = None) -> None:
		"""Mark an alert as acknowledged."""
		doc = frappe.get_doc(_DT, alert_id)
		if doc.status != "Open":
			frappe.throw(_("Only open alerts can be acknowledged."))
		doc.status = "Acknowledged"
		doc.acknowledged_by = user or frappe.session.user
		doc.acknowledged_date = nowdate()
		doc.save()

	@staticmethod
	def resolve_alert(
		alert_id: str,
		resolution_note: str | None = None,
		user: str | None = None,
	) -> None:
		"""Resolve an alert."""
		doc = frappe.get_doc(_DT, alert_id)
		if doc.status not in ("Open", "Acknowledged"):
			frappe.throw(_("Alert is already resolved or dismissed."))
		doc.status = "Resolved"
		doc.resolved_by = user or frappe.session.user
		doc.resolved_date = nowdate()
		if resolution_note:
			doc.add_comment("Info", resolution_note)
		doc.save()

	@staticmethod
	def dismiss_alert(alert_id: str, reason: str | None = None) -> None:
		"""Dismiss an alert (acknowledged but no action needed)."""
		doc = frappe.get_doc(_DT, alert_id)
		if doc.status not in ("Open", "Acknowledged"):
			frappe.throw(_("Alert is already resolved or dismissed."))
		doc.status = "Dismissed"
		if reason:
			doc.notes = reason
		doc.save()

	# ------------------------------------------------------------------
	# Queries
	# ------------------------------------------------------------------

	@staticmethod
	def get_open_alerts(
		patient: str | None = None,
		severity: str | None = None,
		limit: int = 50,
	) -> list[dict]:
		"""Return open/acknowledged alerts, optionally filtered."""
		if not frappe.db.exists("DocType", _DT):
			return []

		filters: dict[str, Any] = {"status": ["in", ["Open", "Acknowledged"]]}
		if patient:
			filters["patient"] = patient
		if severity:
			filters["severity"] = severity

		return frappe.get_all(
			_DT,
			filters=filters,
			fields=[
				"name", "patient", "patient_name", "severity", "alert_type",
				"message", "status", "identified_on", "enrollment", "creation",
			],
			order_by="creation desc",
			limit_page_length=limit,
		)

	@staticmethod
	def get_alert_counts_by_severity(patient: str | None = None) -> dict[str, int]:
		"""Return a count of open alerts grouped by severity."""
		if not frappe.db.exists("DocType", _DT):
			return {}

		filters: dict[str, Any] = {"status": ["in", ["Open", "Acknowledged"]]}
		if patient:
			filters["patient"] = patient

		rows = frappe.get_all(
			_DT,
			filters=filters,
			fields=["severity", "count(name) as cnt"],
			group_by="severity",
		)
		return {row.severity: row.cnt for row in rows}

	@staticmethod
	def get_alerts_for_enrollment(enrollment: str) -> list[dict]:
		"""Return all open/acknowledged alerts for a specific enrollment."""
		if not frappe.db.exists("DocType", _DT):
			return []

		return frappe.get_all(
			_DT,
			filters={
				"enrollment": enrollment,
				"status": ["in", ["Open", "Acknowledged"]],
			},
			fields=[
				"name", "alert_type", "severity", "message",
				"status", "identified_on",
			],
			order_by="severity desc, creation desc",
		)

	# ------------------------------------------------------------------
	# Rule Engine
	# ------------------------------------------------------------------

	@staticmethod
	def evaluate_patient_alerts(patient: str, enrollment: str | None = None) -> list[str]:
		"""Run all alert rules for a patient and create alerts as needed.

		Returns:
			List of newly created alert names.
		"""
		created: list[str] = []

		created.extend(AlertService._check_repeated_high_fasting(patient, enrollment))
		created.extend(AlertService._check_recurrent_hypoglycemia(patient, enrollment))
		created.extend(AlertService._check_overdue_reviews(patient, enrollment))
		created.extend(AlertService._check_weight_regain(patient, enrollment))

		return created

	@staticmethod
	def _check_repeated_high_fasting(
		patient: str, enrollment: str | None
	) -> list[str]:
		"""Trend-based: repeated high fasting glucose."""
		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return []

		if AlertService._has_recent_open_alert(patient, "Repeated High Fasting Glucose"):
			return []

		try:
			from alcura_diabetes_obesity_disease_mgmt.services.diabetes import DiabetesService
			result = DiabetesService.detect_repeated_high_fasting(patient)
			if result["detected"]:
				name = AlertService.create_alert(
					patient=patient,
					severity="High",
					alert_type="Repeated High Fasting Glucose",
					message=_(
						"{0} high fasting glucose readings in the last 30 days."
					).format(result["count"]),
					enrollment=enrollment,
					evidence_summary=f"Count: {result['count']}",
				)
				return [name]
		except Exception:
			pass
		return []

	@staticmethod
	def _check_recurrent_hypoglycemia(
		patient: str, enrollment: str | None
	) -> list[str]:
		"""Frequency-based: recurrent hypoglycemia."""
		if not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return []

		if AlertService._has_recent_open_alert(patient, "Recurrent Hypoglycemia"):
			return []

		try:
			from alcura_diabetes_obesity_disease_mgmt.services.diabetes import DiabetesService
			result = DiabetesService.detect_recurrent_hypoglycemia(patient)
			if result["detected"]:
				name = AlertService.create_alert(
					patient=patient,
					severity="Critical",
					alert_type="Recurrent Hypoglycemia",
					message=_(
						"{0} hypoglycemia events in the last 30 days."
					).format(result["count"]),
					enrollment=enrollment,
					evidence_summary=f"Count: {result['count']}",
				)
				return [name]
		except Exception:
			pass
		return []

	@staticmethod
	def _check_overdue_reviews(
		patient: str, enrollment: str | None
	) -> list[str]:
		"""Missed-event-based: overdue follow-up reviews."""
		if not frappe.db.exists("DocType", "Disease Review Sheet"):
			return []

		if AlertService._has_recent_open_alert(patient, "Missed Follow-Up"):
			return []

		overdue = frappe.get_all(
			"Disease Review Sheet",
			filters={
				"patient": patient,
				"status": "Scheduled",
				"due_date": ["<", nowdate()],
			},
			fields=["name"],
			limit_page_length=1,
		)
		if overdue:
			name = AlertService.create_alert(
				patient=patient,
				severity="Medium",
				alert_type="Missed Follow-Up",
				message=_("Patient has overdue scheduled review(s)."),
				enrollment=enrollment,
			)
			return [name]
		return []

	@staticmethod
	def _check_weight_regain(
		patient: str, enrollment: str | None
	) -> list[str]:
		"""Trend-based: weight regain detection."""
		if not enrollment or not frappe.db.exists("DocType", "Home Monitoring Entry"):
			return []

		if AlertService._has_recent_open_alert(patient, "Weight Regain"):
			return []

		try:
			from alcura_diabetes_obesity_disease_mgmt.services.obesity import ObesityService
			result = ObesityService.detect_regain(patient, enrollment)
			if result["detected"]:
				name = AlertService.create_alert(
					patient=patient,
					severity="Medium",
					alert_type="Weight Regain",
					message=_(
						"Weight regain of {0}% from lowest recorded weight."
					).format(result["regain_pct"]),
					enrollment=enrollment,
					evidence_summary=(
						f"Lowest: {result['lowest_weight']}kg, "
						f"Current: {result['current_weight']}kg"
					),
				)
				return [name]
		except Exception:
			pass
		return []

	@staticmethod
	def _has_recent_open_alert(
		patient: str,
		alert_type: str,
		lookback_days: int = 7,
	) -> bool:
		"""Check if a similar open alert already exists to avoid duplicates."""
		if not frappe.db.exists("DocType", _DT):
			return False

		from_date = add_days(nowdate(), -lookback_days)
		return bool(
			frappe.db.exists(
				_DT,
				{
					"patient": patient,
					"alert_type": alert_type,
					"status": ["in", ["Open", "Acknowledged"]],
					"identified_on": [">=", from_date],
				},
			)
		)
