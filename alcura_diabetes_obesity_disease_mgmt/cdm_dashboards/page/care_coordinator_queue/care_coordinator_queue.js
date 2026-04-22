frappe.pages["care-coordinator-queue"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Care Coordinator Queue"),
		single_column: true,
	});

	page.add_action_item(__("Refresh"), function () {
		load_queue(page);
	});

	load_queue(page);
};

function load_queue(page) {
	page.main.html(
		'<div class="text-center py-5"><span class="spinner-border"></span></div>'
	);

	frappe.call({
		method:
			"alcura_diabetes_obesity_disease_mgmt.services.coordinator.CoordinatorService.get_queue",
		callback: function (r) {
			if (r.message) {
				render_queue(page, r.message);
			}
		},
	});
}

function render_queue(page, items) {
	if (!items.length) {
		page.main.html(
			'<div class="text-center py-5"><p class="text-muted">' +
				__("No items in the queue. All caught up!") +
				"</p></div>"
		);
		return;
	}

	var html = '<div class="container-fluid">';
	html += '<table class="table table-hover">';
	html +=
		"<thead><tr><th>Patient</th><th>Category</th><th>Reason</th><th>Priority</th><th>Action</th></tr></thead>";
	html += "<tbody>";

	items.forEach(function (item) {
		var badge_class =
			item.priority_score >= 80
				? "danger"
				: item.priority_score >= 60
					? "warning"
					: "info";
		html += "<tr>";
		html +=
			"<td><a href='/app/patient/" +
			item.patient +
			"'>" +
			(item.patient_name || item.patient) +
			"</a></td>";
		html += "<td>" + (item.category || "") + "</td>";
		html += "<td>" + (item.reason || "") + "</td>";
		html +=
			'<td><span class="badge badge-' +
			badge_class +
			'">' +
			item.priority_score +
			"</span></td>";
		html +=
			'<td><button class="btn btn-xs btn-primary cdm-log-action" data-patient="' +
			item.patient +
			'">' +
			__("Log Action") +
			"</button></td>";
		html += "</tr>";
	});

	html += "</tbody></table></div>";
	page.main.html(html);

	page.main.find(".cdm-log-action").on("click", function () {
		var patient = $(this).data("patient");
		frappe.new_doc("Care Coordinator Action", { patient: patient });
	});
}
