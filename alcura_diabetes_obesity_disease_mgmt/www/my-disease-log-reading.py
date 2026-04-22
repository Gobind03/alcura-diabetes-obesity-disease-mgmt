"""Context for Log Reading portal page."""

import frappe
from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
from alcura_diabetes_obesity_disease_mgmt.services.portal import PortalService
from alcura_diabetes_obesity_disease_mgmt.api.portal import get_allowed_self_entry_types

no_cache = 1


def get_context(context):
	patient = get_patient_for_user()
	if not patient:
		frappe.throw("Please log in to log a reading.", frappe.PermissionError)

	ctx = PortalService.get_portal_context(patient)
	context.update(ctx)
	context.title = "Log a Reading"
	context.no_breadcrumbs = True
	context.allowed_types = get_allowed_self_entry_types()
