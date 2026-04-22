"""Protocol service — applying evidence-based protocol templates to enrolled patients."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


class ProtocolService:
	"""Manages protocol templates and their application to care plans."""

	@staticmethod
	def apply_protocol(enrollment_id: str, template_id: str) -> str:
		"""Apply a protocol template to an enrollment, generating a care plan.

		Args:
			enrollment_id: The Disease Enrollment document name.
			template_id: The Protocol Template document name.

		Returns:
			The name of the created CDM Care Plan.
		"""
		from alcura_diabetes_obesity_disease_mgmt.services.care_plan import CarePlanService
		from alcura_diabetes_obesity_disease_mgmt.utils.document_helpers import get_cdm_settings

		settings = get_cdm_settings()
		if not settings.enable_protocol_engine:
			frappe.throw(_("Protocol engine is disabled in settings."))

		return CarePlanService.create_care_plan(
			enrollment_id=enrollment_id,
			protocol_template=template_id,
		)

	@staticmethod
	def check_compliance(enrollment_id: str) -> dict[str, Any]:
		"""Evaluate protocol compliance for an enrollment.

		Args:
			enrollment_id: The Disease Enrollment document name.

		Returns:
			Dict with ``compliant`` (bool), ``score`` (float 0-100),
			``gaps`` (list of non-compliant items).
		"""
		# Skeleton — real implementation in a future story
		return {
			"compliant": True,
			"score": 100.0,
			"gaps": [],
			"enrollment": enrollment_id,
		}

	@staticmethod
	def get_applicable_protocols(disease_type: str) -> list[dict]:
		"""Return active protocol templates for a disease type.

		Args:
			disease_type: One of the supported disease types.

		Returns:
			List of protocol template summary dicts.
		"""
		if not frappe.db.exists("DocType", "Protocol Template"):
			return []
		return frappe.get_all(
			"Protocol Template",
			filters={"disease_type": disease_type, "status": "Active"},
			fields=["name", "title", "disease_type", "status"],
			order_by="title asc",
		)

	@staticmethod
	def get_protocol_steps(template_id: str) -> list[dict]:
		"""Return the ordered steps of a protocol template.

		Args:
			template_id: The Protocol Template document name.

		Returns:
			List of step dicts.
		"""
		if not frappe.db.exists("DocType", "Protocol Template"):
			return []
		doc = frappe.get_doc("Protocol Template", template_id)
		return [step.as_dict() for step in (doc.get("steps") or [])]
