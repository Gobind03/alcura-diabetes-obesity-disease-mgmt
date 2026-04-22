app_name = "chronic_disease_management"
app_title = "Chronic Disease Management"
app_publisher = "Alcura"
app_description = "Longitudinal Disease Management for Diabetes, Obesity, and Metabolic Conditions"
app_email = "dev@alcura.io"
app_license = "MIT"
app_version = "0.0.1"

required_apps = ["frappe/erpnext", "frappe/hrms", "healthcare"]

# ---------------------------------------------------------------------------
# App Includes (used to inject assets into Desk / Portal)
# ---------------------------------------------------------------------------

# app_include_css = "/assets/chronic_disease_management/css/chronic_disease_management.css"
# app_include_js = "/assets/chronic_disease_management/js/chronic_disease_management.js"

# web_include_css = "/assets/chronic_disease_management/css/chronic_disease_management_web.css"
# web_include_js = "/assets/chronic_disease_management/js/chronic_disease_management_web.js"

# ---------------------------------------------------------------------------
# DocType-specific JS / CSS
# ---------------------------------------------------------------------------

doctype_js = {
	"Patient": "public/js/patient.js",
	"Patient Encounter": "public/js/patient_encounter.js",
	"Patient Appointment": "public/js/patient_appointment.js",
}

# doctype_list_js = {"DocType Name": "public/js/doctype_name_list.js"}
# doctype_tree_js = {"DocType Name": "public/js/doctype_name_tree.js"}
# doctype_calendar_js = {"DocType Name": "public/js/doctype_name_calendar.js"}

# ---------------------------------------------------------------------------
# Website / Portal
# ---------------------------------------------------------------------------

portal_menu_items = [
	{"title": "My Program", "route": "/my-disease-program", "role": "CDM Patient"},
	{"title": "My Trends", "route": "/my-disease-trends", "role": "CDM Patient"},
	{"title": "Log Reading", "route": "/my-disease-log-reading", "role": "CDM Patient"},
	{"title": "My Goals", "route": "/my-disease-goals", "role": "CDM Patient"},
	{"title": "Upcoming", "route": "/my-disease-upcoming", "role": "CDM Patient"},
]

# website_generators = ["Web Page"]

# webform_include_js = {"Web Form Name": "public/js/web_form.js"}
# webform_include_css = {"Web Form Name": "public/css/web_form.css"}

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

# before_install = "chronic_disease_management.setup.install.before_install"
after_install = "chronic_disease_management.setup.install.after_install"
before_uninstall = "chronic_disease_management.setup.install.before_uninstall"
# after_uninstall = "chronic_disease_management.setup.install.after_uninstall"

# ---------------------------------------------------------------------------
# App lifecycle hooks (run per-app on bench install / uninstall)
# ---------------------------------------------------------------------------

# before_app_install = "chronic_disease_management.setup.install.before_app_install"
# after_app_install = "chronic_disease_management.setup.install.after_app_install"

# ---------------------------------------------------------------------------
# Desk Notifications
# ---------------------------------------------------------------------------

# notification_config = "chronic_disease_management.notifications.get_notification_config"

# ---------------------------------------------------------------------------
# Permissions evaluated in scripted ways
# ---------------------------------------------------------------------------

_cdm_query_conditions = (
	"chronic_disease_management.permissions.cdm_permissions"
	".get_cdm_query_conditions"
)
_cdm_has_permission = (
	"chronic_disease_management.permissions.cdm_permissions"
	".has_cdm_permission"
)

permission_query_conditions = {
	"Disease Enrollment": _cdm_query_conditions,
	"Disease Baseline Assessment": _cdm_query_conditions,
	"CDM Care Plan": _cdm_query_conditions,
	"Disease Goal": _cdm_query_conditions,
	"Disease Review Sheet": _cdm_query_conditions,
	"Home Monitoring Entry": _cdm_query_conditions,
	"CDM Alert": _cdm_query_conditions,
	"Diabetes Profile": _cdm_query_conditions,
	"Obesity Profile": _cdm_query_conditions,
	"Medication Adherence Log": _cdm_query_conditions,
	"Medication Side Effect Log": _cdm_query_conditions,
	"Complication Screening Tracker": _cdm_query_conditions,
	"Care Gap": _cdm_query_conditions,
	"Diet Plan": _cdm_query_conditions,
	"Meal Log": _cdm_query_conditions,
	"Activity Log": _cdm_query_conditions,
	"Supplement Log": _cdm_query_conditions,
	"Care Coordinator Action": _cdm_query_conditions,
}

has_permission = {
	"Disease Enrollment": _cdm_has_permission,
	"Disease Baseline Assessment": _cdm_has_permission,
	"CDM Care Plan": _cdm_has_permission,
	"Disease Goal": _cdm_has_permission,
	"Disease Review Sheet": _cdm_has_permission,
	"Home Monitoring Entry": _cdm_has_permission,
	"CDM Alert": _cdm_has_permission,
	"Diabetes Profile": _cdm_has_permission,
	"Obesity Profile": _cdm_has_permission,
	"Medication Adherence Log": _cdm_has_permission,
	"Medication Side Effect Log": _cdm_has_permission,
	"Complication Screening Tracker": _cdm_has_permission,
	"Care Gap": _cdm_has_permission,
	"Diet Plan": _cdm_has_permission,
	"Meal Log": _cdm_has_permission,
	"Activity Log": _cdm_has_permission,
	"Supplement Log": _cdm_has_permission,
	"Care Coordinator Action": _cdm_has_permission,
}

# ---------------------------------------------------------------------------
# DocType Class overrides
# ---------------------------------------------------------------------------

# override_doctype_class = {
# 	"Patient Encounter": "chronic_disease_management.overrides.patient_encounter.CDMPatientEncounter",
# }

# ---------------------------------------------------------------------------
# Dashboard overrides
# ---------------------------------------------------------------------------

# override_doctype_dashboards = {
# 	"Patient": "chronic_disease_management.overrides.patient_dashboard.get_dashboard_data",
# }

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------

# doc_events = {
# 	"Patient": {
# 		"validate": "chronic_disease_management.overrides.patient_events.validate",
# 	},
# 	"Patient Encounter": {
# 		"on_submit": "chronic_disease_management.overrides.encounter_events.on_submit",
# 	},
# 	"Vital Signs": {
# 		"on_submit": "chronic_disease_management.overrides.vital_signs_events.on_submit",
# 	},
# 	"Lab Test": {
# 		"on_submit": "chronic_disease_management.overrides.lab_test_events.on_submit",
# 	},
# }

# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------

# scheduler_events = {
# 	"cron": {
# 		"0 8 * * *": [
# 			"chronic_disease_management.tasks.send_review_reminders",
# 		],
# 		"*/30 * * * *": [
# 			"chronic_disease_management.tasks.check_monitoring_alerts",
# 		],
# 	},
# 	"daily": [
# 		"chronic_disease_management.tasks.check_overdue_reviews",
# 	],
# 	"weekly": [
# 		"chronic_disease_management.tasks.generate_compliance_summary",
# 	],
# }

# ---------------------------------------------------------------------------
# Override Whitelisted Methods
# ---------------------------------------------------------------------------

# override_whitelisted_methods = {
# 	"healthcare.method.path": "chronic_disease_management.overrides.method_override",
# }

# ---------------------------------------------------------------------------
# Jinja customizations
# ---------------------------------------------------------------------------

# jinja = {
# 	"methods": [
# 		"chronic_disease_management.utils.formatters.format_clinical_value",
# 	],
# }

# ---------------------------------------------------------------------------
# Fixtures (auto-exported / imported on install)
# ---------------------------------------------------------------------------

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "in", [
		"CDM Enrollment",
		"CDM Care Plans",
		"CDM Reviews",
		"CDM Monitoring",
		"CDM Protocols",
		"CDM Shared",
	]]]},
	{"dt": "Property Setter", "filters": [["module", "in", [
		"CDM Enrollment",
		"CDM Care Plans",
		"CDM Reviews",
		"CDM Monitoring",
		"CDM Protocols",
		"CDM Shared",
	]]]},
]

# ---------------------------------------------------------------------------
# User Data Protection (GDPR)
# ---------------------------------------------------------------------------

# user_data_fields = [
# 	{
# 		"doctype": "CDM Enrollment",
# 		"filter_by": "patient_email",
# 		"redact_fields": ["patient_name"],
# 		"partial": True,
# 	},
# ]

# ---------------------------------------------------------------------------
# Authentication and Authorization
# ---------------------------------------------------------------------------

# auth_hooks = [
# 	"chronic_disease_management.auth.validate",
# ]
