"""Audit logging utilities for critical CDM actions.

Uses Frappe's Comment doctype for application-level audit entries alongside
the built-in Version tracking for field-level changes.
"""

from __future__ import annotations

import json
import logging

import frappe
from frappe import _

logger = logging.getLogger("chronic_disease_management.audit")


def log_status_change(
	doctype: str,
	name: str,
	field: str,
	old_value: str,
	new_value: str,
	user: str | None = None,
) -> None:
	"""Record a status change on a CDM document as a Comment.

	This creates a visible audit trail in the document's timeline/activity feed.

	Args:
		doctype: The DocType of the document.
		name: The document name.
		field: The field that changed (e.g., ``"status"``).
		old_value: Previous value.
		new_value: New value.
		user: The user who made the change; defaults to session user.
	"""
	user = user or frappe.session.user
	content = _("Status changed: {0} from '{1}' to '{2}' by {3}").format(
		field, old_value, new_value, user
	)

	frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": doctype,
			"reference_name": name,
			"content": content,
			"comment_by": user,
		}
	).insert(ignore_permissions=True)

	logger.info(
		"CDM Audit: %s %s — %s: '%s' -> '%s' by %s",
		doctype, name, field, old_value, new_value, user,
	)


def log_critical_action(
	action_type: str,
	details: str | dict,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	user: str | None = None,
) -> None:
	"""Log a critical action that may not be tied to a status change.

	Examples: protocol override, alert dismissal, manual goal revision,
	permission escalation.

	Args:
		action_type: Category label (e.g., ``"Protocol Override"``, ``"Alert Dismissed"``).
		details: Free-text or dict with structured details.
		reference_doctype: Optional associated doctype.
		reference_name: Optional associated document name.
		user: The user who performed the action; defaults to session user.
	"""
	user = user or frappe.session.user

	if isinstance(details, dict):
		details_str = json.dumps(details, default=str)
	else:
		details_str = str(details)

	content = _("CDM Critical Action — {0}: {1}").format(action_type, details_str)

	comment_data: dict = {
		"doctype": "Comment",
		"comment_type": "Info",
		"content": content,
		"comment_by": user,
	}
	if reference_doctype and reference_name:
		comment_data["reference_doctype"] = reference_doctype
		comment_data["reference_name"] = reference_name

	frappe.get_doc(comment_data).insert(ignore_permissions=True)

	logger.warning(
		"CDM Critical Action: [%s] %s — ref: %s/%s — user: %s",
		action_type, details_str, reference_doctype, reference_name, user,
	)


def get_audit_trail(
	doctype: str,
	name: str,
	limit: int = 50,
) -> list[dict]:
	"""Retrieve the CDM audit trail (Comment records) for a document.

	Args:
		doctype: The DocType.
		name: The document name.
		limit: Maximum entries to return.

	Returns:
		List of comment dicts with ``content``, ``comment_by``, ``creation``.
	"""
	return frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"comment_type": "Info",
			"content": ["like", "%CDM%"],
		},
		fields=["content", "comment_by", "creation"],
		order_by="creation desc",
		limit_page_length=limit,
	)
