"""Context for My Disease Goals portal page."""

import frappe
from chronic_disease_management.permissions.cdm_permissions import get_patient_for_user
from chronic_disease_management.services.portal import PortalService

no_cache = 1


def get_context(context):
	patient = get_patient_for_user()
	if not patient:
		frappe.throw("Please log in to view your goals.", frappe.PermissionError)

	data = PortalService.get_goals_page_data(patient)
	context.update(data)
	context.title = "My Goals"
	context.no_breadcrumbs = True
