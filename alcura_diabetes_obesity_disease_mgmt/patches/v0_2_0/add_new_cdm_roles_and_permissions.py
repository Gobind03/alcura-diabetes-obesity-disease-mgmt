"""Post-model-sync patch: ensure CDM roles exist and permissions are applied.

Runs after the new DocTypes are synced so the permission matrix
can be applied cleanly.
"""

import frappe

from alcura_diabetes_obesity_disease_mgmt.constants.roles import ALL_CDM_ROLES
from alcura_diabetes_obesity_disease_mgmt.permissions.role_matrix import (
	PERMISSION_MATRIX,
	apply_permissions,
)


def execute():
	for role_name in ALL_CDM_ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(
				ignore_permissions=True
			)

	for doctype in PERMISSION_MATRIX:
		if frappe.db.exists("DocType", doctype):
			try:
				apply_permissions(doctype)
			except Exception:
				frappe.log_error(f"CDM: Failed to apply permissions for {doctype}")

	frappe.db.commit()
