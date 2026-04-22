from frappe import _


def get_data():
	return [
		{
			"module_name": "CDM Enrollment",
			"color": "green",
			"icon": "octicon octicon-person",
			"type": "module",
			"label": _("CDM Enrollment"),
		},
		{
			"module_name": "CDM Care Plans",
			"color": "blue",
			"icon": "octicon octicon-checklist",
			"type": "module",
			"label": _("CDM Care Plans"),
		},
		{
			"module_name": "CDM Reviews",
			"color": "orange",
			"icon": "octicon octicon-clock",
			"type": "module",
			"label": _("CDM Reviews"),
		},
		{
			"module_name": "CDM Monitoring",
			"color": "red",
			"icon": "octicon octicon-pulse",
			"type": "module",
			"label": _("CDM Monitoring"),
		},
		{
			"module_name": "CDM Dashboards",
			"color": "purple",
			"icon": "octicon octicon-graph",
			"type": "module",
			"label": _("CDM Dashboards"),
		},
		{
			"module_name": "CDM Reports",
			"color": "grey",
			"icon": "octicon octicon-file",
			"type": "module",
			"label": _("CDM Reports"),
		},
		{
			"module_name": "CDM Protocols",
			"color": "cyan",
			"icon": "octicon octicon-book",
			"type": "module",
			"label": _("CDM Protocols"),
		},
	]
