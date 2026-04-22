frappe.pages["patient-chronic-disease-cockpit"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Patient Chronic Disease Cockpit"),
		single_column: true,
	});

	page.patient_field = page.add_field({
		fieldname: "patient",
		label: __("Patient"),
		fieldtype: "Link",
		options: "Patient",
		reqd: 1,
		change: function () {
			var patient = page.patient_field.get_value();
			if (patient) {
				load_cockpit(page, patient);
			}
		},
	});

	page.add_action_item(__("Open Care Plan"), function () {
		if (page._enrollment) {
			frappe.set_route("List", "CDM Care Plan", { enrollment: page._enrollment });
		}
	});

	page.add_action_item(__("Create Review"), function () {
		if (page._patient) {
			frappe.new_doc("Disease Review Sheet", { patient: page._patient });
		}
	});

	page.add_action_item(__("View Monitoring History"), function () {
		if (page._patient) {
			frappe.set_route("List", "Home Monitoring Entry", { patient: page._patient });
		}
	});

	var params = frappe.utils.get_url_params();
	if (params.patient) {
		page.patient_field.set_value(params.patient);
	}
};

function load_cockpit(page, patient) {
	page._patient = patient;
	page.main.html('<div class="text-center py-5"><span class="spinner-border"></span></div>');

	frappe.call({
		method:
			"chronic_disease_management.services.dashboard.DashboardService.get_patient_cockpit",
		args: { patient: patient },
		callback: function (r) {
			if (r.message) {
				render_cockpit(page, r.message);
			}
		},
	});
}

function render_cockpit(page, data) {
	page._enrollment = data.enrollment_summary ? data.enrollment_summary.name : null;

	var html = '<div class="cdm-cockpit container-fluid">';

	// Enrollment card
	var enr = data.enrollment_summary || {};
	html += '<div class="row mb-3">';
	html += '<div class="col-md-6"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Enrollment") + "</h5>";
	if (enr.name) {
		html +=
			"<p><strong>" + (enr.disease_type || "") + "</strong> — " + (enr.program_status || "") + "</p>";
		html += "<p>Enrolled: " + (enr.enrollment_date || "") + "</p>";
		html += "<p>Practitioner: " + (enr.practitioner_name || "—") + "</p>";
	} else {
		html += '<p class="text-muted">' + __("No active enrollment") + "</p>";
	}
	html += "</div></div></div>";

	// Care Plan card
	var cp = data.care_plan_summary || {};
	html += '<div class="col-md-6"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Care Plan") + "</h5>";
	if (cp.name) {
		html += "<p>Status: " + (cp.status || "") + "</p>";
		if (cp.plan_summary) html += "<p>" + cp.plan_summary.substring(0, 200) + "</p>";
	} else {
		html += '<p class="text-muted">' + __("No active care plan") + "</p>";
	}
	html += "</div></div></div></div>";

	// Goals
	html += '<div class="row mb-3"><div class="col-12"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Goals") + "</h5>";
	var goals = data.goals_summary || [];
	if (goals.length) {
		html += '<table class="table table-sm"><thead><tr><th>Metric</th><th>Target</th><th>Current</th><th>Status</th></tr></thead><tbody>';
		goals.forEach(function (g) {
			html +=
				"<tr><td>" + g.goal_metric + "</td><td>" + (g.target_value || "—") + "</td><td>" + (g.current_value || "—") + "</td><td>" + g.status + "</td></tr>";
		});
		html += "</tbody></table>";
	} else {
		html += '<p class="text-muted">' + __("No goals defined") + "</p>";
	}
	html += "</div></div></div></div>";

	// Alerts
	html += '<div class="row mb-3"><div class="col-md-6"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Active Alerts") + "</h5>";
	var alerts = data.alerts || [];
	if (alerts.length) {
		alerts.forEach(function (a) {
			var color = a.severity === "Critical" ? "danger" : a.severity === "High" ? "warning" : "info";
			html +=
				'<div class="alert alert-' + color + ' py-1 px-2 mb-1"><small><strong>' + a.alert_type + "</strong> — " + a.message + "</small></div>";
		});
	} else {
		html += '<p class="text-muted">' + __("No active alerts") + "</p>";
	}
	html += "</div></div></div>";

	// Care Gaps
	html += '<div class="col-md-6"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Care Gaps") + "</h5>";
	var gaps = data.care_gaps || [];
	if (gaps.length) {
		gaps.forEach(function (g) {
			html +=
				'<div class="mb-1"><span class="badge badge-' + (g.severity === "High" ? "danger" : "warning") + '">' + g.severity + "</span> " + g.title + "</div>";
		});
	} else {
		html += '<p class="text-muted">' + __("No open care gaps") + "</p>";
	}
	html += "</div></div></div></div>";

	// Recent reviews
	html += '<div class="row mb-3"><div class="col-12"><div class="card"><div class="card-body">';
	html += "<h5>" + __("Recent Reviews") + "</h5>";
	var reviews = data.recent_reviews || [];
	if (reviews.length) {
		html += '<table class="table table-sm"><thead><tr><th>Type</th><th>Date</th><th>Practitioner</th></tr></thead><tbody>';
		reviews.forEach(function (rv) {
			html +=
				"<tr><td><a href='/app/disease-review-sheet/" + rv.name + "'>" + rv.review_type + "</a></td><td>" + (rv.review_date || "") + "</td><td>" + (rv.practitioner_name || "—") + "</td></tr>";
		});
		html += "</tbody></table>";
	} else {
		html += '<p class="text-muted">' + __("No completed reviews") + "</p>";
	}
	html += "</div></div></div></div>";

	html += "</div>";
	page.main.html(html);
}
