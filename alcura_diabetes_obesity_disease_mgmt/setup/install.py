"""Lifecycle hooks executed during app install / uninstall."""

from __future__ import annotations

import frappe


def after_install():
	"""Runs once after the app is installed on a site."""
	from alcura_diabetes_obesity_disease_mgmt.setup.custom_fields import setup_custom_fields
	from alcura_diabetes_obesity_disease_mgmt.setup.roles import setup_roles

	setup_roles()
	setup_custom_fields()
	_create_default_settings()
	_verify_healthcare_compatibility()
	frappe.logger("alcura_diabetes_obesity_disease_mgmt").info(
		"Alcura Disease Management app installed successfully."
	)


def before_uninstall():
	"""Cleanup before the app is removed from a site."""
	from alcura_diabetes_obesity_disease_mgmt.setup.custom_fields import teardown_custom_fields
	from alcura_diabetes_obesity_disease_mgmt.setup.roles import teardown_roles

	teardown_custom_fields()
	teardown_roles()
	frappe.logger("alcura_diabetes_obesity_disease_mgmt").info(
		"Alcura Disease Management: custom fields and roles removed."
	)


def _create_default_settings():
	"""Create the Disease Management Settings singleton with sensible defaults.

	Idempotent — skips if the document already has enabled programs.
	"""
	from alcura_diabetes_obesity_disease_mgmt.constants.disease_types import SUPPORTED_DISEASE_TYPES

	if not frappe.db.exists("DocType", "Disease Management Settings"):
		return

	settings = frappe.get_single("Disease Management Settings")
	if settings.enabled_programs:
		return

	for disease_type in SUPPORTED_DISEASE_TYPES:
		settings.append("enabled_programs", {"disease_type": disease_type})

	default_self_entry_types = [
		"Blood Glucose",
		"Blood Pressure",
		"Weight",
	]
	for entry_type in default_self_entry_types:
		settings.append("allowed_self_entry_types", {"entry_type": entry_type})

	settings.flags.ignore_permissions = True
	settings.save()
	frappe.db.commit()


def _verify_healthcare_compatibility():
	"""Log warnings if expected Healthcare doctypes are missing."""
	expected_doctypes = [
		"Patient",
		"Patient Encounter",
		"Vital Signs",
		"Lab Test",
		"Lab Test Template",
		"Patient Appointment",
		"Healthcare Practitioner",
	]
	missing = [dt for dt in expected_doctypes if not frappe.db.exists("DocType", dt)]
	if missing:
		frappe.logger("alcura_diabetes_obesity_disease_mgmt").warning(
			"Healthcare doctypes not found (some CDM features may be limited): %s",
			", ".join(missing),
		)
