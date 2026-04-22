"""CDM Care Plan controller.

Manages the lifecycle of individualized care plans linked to disease enrollments.
Enforces single-active-plan constraint, status transitions, and renders linked
goal summaries for at-a-glance clinical review.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from chronic_disease_management.constants.statuses import CarePlanStatus
from chronic_disease_management.utils.validators import validate_care_plan_status_transition


class CDMCarePlan(Document):

	def before_insert(self):
		self._enforce_single_active_plan()

	def validate(self):
		self._set_patient_from_enrollment()
		self._set_practitioner_name()
		self._validate_start_date()

	def before_save(self):
		if self.has_value_changed("status") and not self.is_new():
			old_status = self.get_db_value("status")
			if old_status:
				validate_care_plan_status_transition(old_status, self.status)

	def on_update(self):
		self.render_goals_html()

	def on_trash(self):
		self._prevent_delete_with_active_goals()

	# ------------------------------------------------------------------
	# Validation helpers
	# ------------------------------------------------------------------

	def _enforce_single_active_plan(self) -> None:
		"""Prevent multiple active care plans per enrollment unless configured."""
		if not self.enrollment:
			return

		allow_multiple = frappe.db.get_single_value(
			"Disease Management Settings", "allow_multiple_active_care_plans"
		)
		if allow_multiple:
			return

		existing = frappe.db.exists(
			"CDM Care Plan",
			{
				"enrollment": self.enrollment,
				"status": ["in", [CarePlanStatus.ACTIVE, CarePlanStatus.DRAFT]],
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("Enrollment {0} already has an active or draft care plan ({1}). "
				  "Only one active care plan per enrollment is allowed.").format(
					self.enrollment, existing
				),
				frappe.DuplicateEntryError,
			)

	def _set_patient_from_enrollment(self) -> None:
		if self.enrollment and not self.patient:
			self.patient = frappe.db.get_value(
				"Disease Enrollment", self.enrollment, "patient"
			)
		if self.enrollment and not self.patient_name:
			self.patient_name = frappe.db.get_value(
				"Disease Enrollment", self.enrollment, "patient_name"
			)
		if self.enrollment and not self.disease_type:
			self.disease_type = frappe.db.get_value(
				"Disease Enrollment", self.enrollment, "disease_type"
			)

	def _set_practitioner_name(self) -> None:
		if self.practitioner and not self.practitioner_name:
			self.practitioner_name = frappe.db.get_value(
				"Healthcare Practitioner", self.practitioner, "practitioner_name"
			)

	def _validate_start_date(self) -> None:
		if self.start_date and getdate(self.start_date) > getdate(nowdate()):
			frappe.throw(
				_("Start date cannot be in the future."),
				frappe.ValidationError,
			)

	def _prevent_delete_with_active_goals(self) -> None:
		if not frappe.db.exists("DocType", "Disease Goal"):
			return
		active_goals = frappe.db.count(
			"Disease Goal",
			{"care_plan": self.name, "status": ["not in", ["Revised", "Not Met"]]},
		)
		if active_goals:
			frappe.throw(
				_("Cannot delete care plan with {0} active goal(s). "
				  "Mark goals as Not Met or revise them first.").format(active_goals),
				frappe.ValidationError,
			)

	# ------------------------------------------------------------------
	# Goals HTML rendering
	# ------------------------------------------------------------------

	def render_goals_html(self) -> None:
		"""Re-render the goals_html field from linked Disease Goal records."""
		if not frappe.db.exists("DocType", "Disease Goal"):
			return

		goals = frappe.get_all(
			"Disease Goal",
			filters={"care_plan": self.name, "status": ["!=", "Revised"]},
			fields=[
				"name", "goal_type", "goal_metric", "target_value",
				"target_range_low", "target_range_high", "target_unit",
				"current_value", "status", "effective_date", "review_date",
			],
			order_by="goal_type asc, effective_date asc",
		)

		if not goals:
			html = '<p class="text-muted">No goals defined yet.</p>'
		else:
			html = self._build_goals_table(goals)

		frappe.db.set_value(
			"CDM Care Plan", self.name, "goals_html", html, update_modified=False
		)

	@staticmethod
	def _build_goals_table(goals: list[dict]) -> str:
		status_colors = {
			"Not Started": "gray",
			"In Progress": "blue",
			"Achieved": "green",
			"Partially Met": "orange",
			"Not Met": "red",
			"Revised": "gray",
		}

		rows = []
		for g in goals:
			target = g.get("target_value") or ""
			if not target and g.get("target_range_low") is not None:
				target = f"{g['target_range_low']} – {g['target_range_high']}"
			if g.get("target_unit"):
				target += f" {g['target_unit']}"

			current = g.get("current_value") or "—"
			color = status_colors.get(g["status"], "gray")
			badge = f'<span class="indicator-pill {color}">{g["status"]}</span>'

			rows.append(
				f"<tr>"
				f"<td><a href='/app/disease-goal/{g['name']}'>{g['goal_metric']}</a></td>"
				f"<td>{target}</td>"
				f"<td>{current}</td>"
				f"<td>{badge}</td>"
				f"</tr>"
			)

		return (
			'<table class="table table-sm table-bordered">'
			"<thead><tr>"
			"<th>Metric</th><th>Target</th><th>Current</th><th>Status</th>"
			"</tr></thead>"
			f"<tbody>{''.join(rows)}</tbody></table>"
		)
