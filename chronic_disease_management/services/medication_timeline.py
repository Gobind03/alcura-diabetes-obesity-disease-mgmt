"""Medication timeline service — normalize medication events from multiple sources."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from chronic_disease_management.adapters.base import optional_doctype, safe_get_all


class MedicationTimelineService:
	"""Normalizes medication history from Medication Request and Drug Prescription
	into a unified timeline event list."""

	@staticmethod
	def get_timeline_events(
		patient: str,
		from_date: str | None = None,
		to_date: str | None = None,
	) -> list[dict[str, Any]]:
		"""Return a chronologically sorted list of normalized medication events.

		Each event has: medication_name, medication_class, source_doctype,
		source_name, start_date, stop_date, is_active, dose_text, route,
		frequency, change_type, notes.
		"""
		events: list[dict[str, Any]] = []
		events.extend(MedicationTimelineService._from_medication_requests(patient, from_date, to_date))
		events.extend(MedicationTimelineService._from_drug_prescriptions(patient, from_date, to_date))

		events.sort(key=lambda e: e.get("start_date") or "0000-00-00", reverse=True)
		return events

	@staticmethod
	def get_active_medications(patient: str) -> list[dict[str, Any]]:
		"""Return only currently active medications as normalized events."""
		events = MedicationTimelineService.get_timeline_events(patient)
		return [e for e in events if e.get("is_active")]

	@staticmethod
	def get_medication_periods(
		patient: str,
		medication_name: str | None = None,
	) -> list[dict[str, Any]]:
		"""Return medication start/stop periods for overlay charting.

		Each period has: medication_name, start_date, stop_date, is_active.
		"""
		events = MedicationTimelineService.get_timeline_events(patient)
		periods = []
		for e in events:
			if medication_name and e.get("medication_name") != medication_name:
				continue
			periods.append({
				"medication_name": e.get("medication_name"),
				"start_date": e.get("start_date"),
				"stop_date": e.get("stop_date"),
				"is_active": e.get("is_active"),
				"dose_text": e.get("dose_text"),
			})
		return periods

	# ------------------------------------------------------------------
	# Private normalizers
	# ------------------------------------------------------------------

	@staticmethod
	def _from_medication_requests(
		patient: str,
		from_date: str | None = None,
		to_date: str | None = None,
	) -> list[dict[str, Any]]:
		if not optional_doctype("Medication Request"):
			return []

		filters: dict[str, Any] = {"patient": patient}
		if from_date and to_date:
			filters["order_date"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["order_date"] = [">=", from_date]

		rows = safe_get_all(
			"Medication Request",
			filters=filters,
			fields=[
				"name", "medication", "medication_item", "status",
				"order_date", "practitioner_name", "dosage", "period",
				"dosage_form",
			],
			order_by="order_date desc",
		)

		events = []
		for r in rows:
			med_name = r.get("medication") or r.get("medication_item") or "Unknown"
			is_active = (r.get("status") or "").lower() in ("active", "draft")

			change_type = "Started"
			if not is_active:
				change_type = "Stopped"

			events.append({
				"medication_name": med_name,
				"medication_class": None,
				"source_doctype": "Medication Request",
				"source_name": r.name,
				"start_date": r.get("order_date"),
				"stop_date": None,
				"is_active": is_active,
				"dose_text": r.get("dosage") or "",
				"route": r.get("dosage_form") or "",
				"frequency": r.get("period") or "",
				"change_type": change_type,
				"notes": None,
			})
		return events

	@staticmethod
	def _from_drug_prescriptions(
		patient: str,
		from_date: str | None = None,
		to_date: str | None = None,
	) -> list[dict[str, Any]]:
		if not optional_doctype("Drug Prescription") or not optional_doctype("Patient Encounter"):
			return []

		enc_filters: dict[str, Any] = {"patient": patient, "docstatus": 1}
		if from_date and to_date:
			enc_filters["encounter_date"] = ["between", [from_date, to_date]]
		elif from_date:
			enc_filters["encounter_date"] = [">=", from_date]

		encounters = frappe.get_all(
			"Patient Encounter",
			filters=enc_filters,
			fields=["name", "encounter_date"],
			order_by="encounter_date desc",
			limit_page_length=50,
		)

		events = []
		for enc in encounters:
			rxs = frappe.get_all(
				"Drug Prescription",
				filters={"parent": enc.name, "parenttype": "Patient Encounter"},
				fields=["drug_code", "drug_name", "dosage", "period", "dosage_form"],
				order_by="idx asc",
			)
			for rx in rxs:
				events.append({
					"medication_name": rx.get("drug_name") or rx.get("drug_code") or "Unknown",
					"medication_class": None,
					"source_doctype": "Patient Encounter",
					"source_name": enc.name,
					"start_date": enc.get("encounter_date"),
					"stop_date": None,
					"is_active": True,
					"dose_text": rx.get("dosage") or "",
					"route": rx.get("dosage_form") or "",
					"frequency": rx.get("period") or "",
					"change_type": "Continued",
					"notes": None,
				})
		return events
