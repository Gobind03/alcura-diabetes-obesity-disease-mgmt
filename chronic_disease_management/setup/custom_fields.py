"""Custom Field definitions added to existing Healthcare / ERPNext doctypes.

Fields are created programmatically during install and exported via the
fixtures hook in hooks.py.  Each field sets module = "CDM Shared" so that
``bench export-fixtures`` picks them up automatically.
"""

MODULE = "CDM Shared"


def get_custom_fields() -> dict[str, list[dict]]:
	"""Return a mapping of DocType -> list of field definitions."""
	return {
		"Patient": [
			{
				"fieldname": "cdm_section_break",
				"fieldtype": "Section Break",
				"label": "Chronic Disease Management",
				"insert_after": "status",
				"collapsible": 1,
				"module": MODULE,
			},
			{
				"fieldname": "cdm_enrolled",
				"fieldtype": "Check",
				"label": "CDM Enrolled",
				"insert_after": "cdm_section_break",
				"read_only": 1,
				"description": "Automatically set when the patient has an active CDM enrollment",
				"module": MODULE,
			},
			{
				"fieldname": "cdm_active_programs",
				"fieldtype": "Small Text",
				"label": "Active CDM Programs",
				"insert_after": "cdm_enrolled",
				"read_only": 1,
				"description": "Comma-separated list of active disease management programs",
				"module": MODULE,
			},
		],
	}


def setup_custom_fields():
	"""Create all CDM custom fields on the target doctypes."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	custom_fields = get_custom_fields()
	if custom_fields:
		create_custom_fields(custom_fields)


def teardown_custom_fields():
	"""Remove CDM custom fields during uninstall."""
	import frappe

	custom_fields = get_custom_fields()
	for dt, fields in custom_fields.items():
		for field_def in fields:
			name = f"{dt}-{field_def['fieldname']}"
			if frappe.db.exists("Custom Field", name):
				frappe.delete_doc("Custom Field", name, force=True)
