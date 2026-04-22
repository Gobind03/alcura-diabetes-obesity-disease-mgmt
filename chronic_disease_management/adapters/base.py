"""Base adapter with compatibility guards for Healthcare doctype access.

Provides caching and graceful degradation when expected doctypes or fields
are absent in the target environment (e.g., different Marley Health version).
"""

from __future__ import annotations

import functools
import logging
from typing import Any

import frappe

logger = logging.getLogger("chronic_disease_management.adapters")


class CDMDependencyError(Exception):
	"""Raised when a required Healthcare doctype or field is missing."""

	def __init__(self, message: str, doctype: str | None = None, field: str | None = None):
		self.doctype = doctype
		self.field = field
		super().__init__(message)


@functools.lru_cache(maxsize=64)
def doctype_exists(doctype_name: str) -> bool:
	"""Check whether a doctype is registered in the current site (cached).

	The result is cached for the lifetime of the worker process. In development
	you can call ``doctype_exists.cache_clear()`` to reset.
	"""
	try:
		return bool(frappe.db.exists("DocType", doctype_name))
	except Exception:
		return False


def field_exists(doctype: str, fieldname: str) -> bool:
	"""Check whether a specific field exists on a doctype's schema.

	Works for both standard and custom fields. Not cached because schema
	changes are infrequent but should be detected promptly.
	"""
	if not doctype_exists(doctype):
		return False
	try:
		meta = frappe.get_meta(doctype)
		return meta.has_field(fieldname)
	except Exception:
		return False


def require_doctype(doctype_name: str) -> None:
	"""Raise ``CDMDependencyError`` if the doctype is not available.

	Use this at the top of adapter methods that cannot function without
	a specific doctype.
	"""
	if not doctype_exists(doctype_name):
		raise CDMDependencyError(
			f"Required Healthcare doctype '{doctype_name}' is not installed. "
			f"Ensure the Marley Health (healthcare) app is installed and up to date.",
			doctype=doctype_name,
		)


def optional_doctype(doctype_name: str) -> bool:
	"""Return ``True`` if the doctype exists, ``False`` with a logged warning otherwise.

	Use for features that degrade gracefully when a doctype is absent.
	"""
	if doctype_exists(doctype_name):
		return True
	logger.warning(
		"Optional Healthcare doctype '%s' is not available. "
		"Some CDM features may be limited.",
		doctype_name,
	)
	return False


def require_field(doctype: str, fieldname: str) -> None:
	"""Raise ``CDMDependencyError`` if a field is missing from a doctype.

	Use when the adapter relies on a specific field that may have been
	removed or renamed in a newer Marley Health version.
	"""
	require_doctype(doctype)
	if not field_exists(doctype, fieldname):
		raise CDMDependencyError(
			f"Required field '{fieldname}' not found on '{doctype}'. "
			f"The Healthcare app schema may have changed.",
			doctype=doctype,
			field=fieldname,
		)


def safe_get_all(
	doctype: str,
	filters: dict | None = None,
	fields: list[str] | None = None,
	order_by: str | None = None,
	limit_page_length: int | None = None,
	**kwargs: Any,
) -> list[dict]:
	"""Wrapper around ``frappe.get_all`` that returns ``[]`` if the doctype is missing."""
	if not doctype_exists(doctype):
		return []
	return frappe.get_all(
		doctype,
		filters=filters,
		fields=fields or ["name"],
		order_by=order_by,
		limit_page_length=limit_page_length,
		**kwargs,
	)


def safe_get_value(
	doctype: str,
	filters: str | dict,
	fieldname: str | list[str],
	as_dict: bool = False,
	order_by: str | None = None,
) -> Any:
	"""Wrapper around ``frappe.db.get_value`` that returns ``None`` if the doctype is missing."""
	if not doctype_exists(doctype):
		return None
	return frappe.db.get_value(
		doctype,
		filters,
		fieldname,
		as_dict=as_dict,
		order_by=order_by,
	)
