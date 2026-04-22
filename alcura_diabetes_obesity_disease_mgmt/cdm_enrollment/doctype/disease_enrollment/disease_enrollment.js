frappe.ui.form.on("Disease Enrollment", {
	refresh(frm) {
		frm.events.set_status_indicator(frm);
		frm.events.add_status_buttons(frm);
		frm.events.add_baseline_button(frm);
		frm.events.render_connections(frm);
	},

	patient(frm) {
		if (!frm.doc.patient) {
			frm.set_value("patient_name", "");
			frm.set_value("patient_age", "");
			frm.set_value("patient_sex", "");
			return;
		}
		frappe.db.get_value("Patient", frm.doc.patient, [
			"patient_name", "sex", "dob",
		]).then((r) => {
			if (!r.message) return;
			const data = r.message;
			frm.set_value("patient_name", data.patient_name || "");
			frm.set_value("patient_sex", data.sex || "");
			if (data.dob) {
				const age = frappe.datetime.get_diff(frappe.datetime.nowdate(), data.dob);
				frm.set_value("patient_age", Math.floor(age / 365) + " years");
			}
		});
	},

	practitioner(frm) {
		if (!frm.doc.practitioner) {
			frm.set_value("practitioner_name", "");
			return;
		}
		frappe.db.get_value(
			"Healthcare Practitioner",
			frm.doc.practitioner,
			"practitioner_name"
		).then((r) => {
			if (r.message) {
				frm.set_value("practitioner_name", r.message.practitioner_name || "");
			}
		});
	},

	set_status_indicator(frm) {
		const STATUS_COLORS = {
			"Draft": "blue",
			"Active": "green",
			"On Hold": "orange",
			"Completed": "darkgrey",
			"Withdrawn": "red",
		};
		const color = STATUS_COLORS[frm.doc.program_status] || "blue";
		frm.page.set_indicator(frm.doc.program_status, color);
	},

	add_status_buttons(frm) {
		if (frm.is_new() || !frm.doc.program_status) return;

		const transitions = {
			"Draft": [
				{ label: __("Activate"), status: "Active", icon: "play" },
				{ label: __("Withdraw"), status: "Withdrawn", icon: "remove" },
			],
			"Active": [
				{ label: __("Suspend"), status: "On Hold", icon: "pause" },
				{ label: __("Complete"), status: "Completed", icon: "check" },
				{ label: __("Withdraw"), status: "Withdrawn", icon: "remove" },
			],
			"On Hold": [
				{ label: __("Reactivate"), status: "Active", icon: "play" },
				{ label: __("Withdraw"), status: "Withdrawn", icon: "remove" },
			],
		};

		const actions = transitions[frm.doc.program_status] || [];
		actions.forEach(({ label, status }) => {
			frm.add_custom_button(label, () => {
				frm.events.transition_status(frm, status);
			}, __("Change Status"));
		});
	},

	transition_status(frm, new_status) {
		const terminal = ["Completed", "Withdrawn"];
		const needs_reason = terminal.includes(new_status) || new_status === "On Hold";

		const do_transition = (reason) => {
			frappe.call({
				method: "alcura_diabetes_obesity_disease_mgmt.api.enrollment.update_enrollment_status",
				args: {
					enrollment: frm.doc.name,
					new_status: new_status,
					reason: reason || "",
				},
				callback(r) {
					if (!r.exc) {
						frm.reload_doc();
					}
				},
			});
		};

		if (needs_reason) {
			frappe.prompt(
				{
					fieldname: "reason",
					fieldtype: "Small Text",
					label: __("Reason"),
					reqd: 1,
				},
				(values) => do_transition(values.reason),
				__("Status Change Reason"),
				__("Confirm")
			);
		} else {
			do_transition("");
		}
	},

	add_baseline_button(frm) {
		if (frm.is_new() || frm.doc.program_status === "Draft") return;

		frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Disease Baseline Assessment",
				filters: { enrollment: frm.doc.name },
			},
			async: false,
			callback(r) {
				if (r.message && r.message > 0) {
					frm.add_custom_button(__("View Baseline Assessment"), () => {
						frappe.set_route("List", "Disease Baseline Assessment", {
							enrollment: frm.doc.name,
						});
					});
				} else {
					frm.add_custom_button(__("Create Baseline Assessment"), () => {
						frappe.call({
							method: "alcura_diabetes_obesity_disease_mgmt.api.enrollment.create_baseline_assessment",
							args: { enrollment: frm.doc.name },
							callback(r2) {
								if (r2.message) {
									frappe.set_route("Form", "Disease Baseline Assessment", r2.message);
								}
							},
						});
					});
				}
			},
		});
	},

	render_connections(frm) {
		if (frm.is_new()) return;

		const $wrapper = frm.fields_dict.connections_html.$wrapper;
		$wrapper.empty();

		const links = [];

		frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Disease Baseline Assessment",
				filters: { enrollment: frm.doc.name },
			},
			async: false,
			callback(r) {
				if (r.message && r.message > 0) {
					links.push(
						`<a class="btn btn-xs btn-default" onclick="frappe.set_route('List','Disease Baseline Assessment',{enrollment:'${frm.doc.name}'})">` +
						`<i class="fa fa-file-text-o"></i> Baseline Assessment (${r.message})</a>`
					);
				}
			},
		});

		if (links.length) {
			$wrapper.html(`<div class="cdm-connections">${links.join(" ")}</div>`);
		} else {
			$wrapper.html(
				'<div class="text-muted small">No connected records yet.</div>'
			);
		}
	},
});
