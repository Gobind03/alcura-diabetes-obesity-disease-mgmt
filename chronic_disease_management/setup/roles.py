"""Role setup for CDM-specific access control."""

import frappe

from chronic_disease_management.constants.roles import ALL_CDM_ROLES, PORTAL_ROLES


def setup_roles():
	"""Create CDM roles if they do not already exist."""
	for role_name in ALL_CDM_ROLES:
		if not frappe.db.exists("Role", role_name):
			role = frappe.new_doc("Role")
			role.role_name = role_name
			role.desk_access = 0 if role_name in PORTAL_ROLES else 1
			role.is_custom = 1
			role.insert(ignore_permissions=True)
	frappe.db.commit()


def teardown_roles():
	"""Remove CDM roles during uninstall."""
	for role_name in ALL_CDM_ROLES:
		if frappe.db.exists("Role", role_name):
			frappe.delete_doc("Role", role_name, force=True)
	frappe.db.commit()
