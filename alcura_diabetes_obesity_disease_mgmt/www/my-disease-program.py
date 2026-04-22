"""Context for My Disease Program portal page."""

import frappe
from alcura_diabetes_obesity_disease_mgmt.permissions.cdm_permissions import get_patient_for_user
from alcura_diabetes_obesity_disease_mgmt.services.portal import PortalService

no_cache = 1


def get_context(context):
	patient = get_patient_for_user()
	if not patient:
		frappe.throw("Please log in to view your program.", frappe.PermissionError)

	data = PortalService.get_program_page_data(patient)
	context.update(data)
	context.title = "My Disease Program"
	context.no_breadcrumbs = True
