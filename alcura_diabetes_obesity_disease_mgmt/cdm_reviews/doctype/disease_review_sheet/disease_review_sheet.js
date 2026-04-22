frappe.ui.form.on("Disease Review Sheet", {
	refresh(frm) {
		frm.events.set_status_indicator(frm);
		frm.events.add_status_buttons(frm);
	},

	set_status_indicator(frm) {
		const colors = {
			Draft: "orange",
			Scheduled: "blue",
			"In Progress": "cyan",
			Completed: "green",
			Missed: "red",
			Rescheduled: "yellow",
			Cancelled: "darkgrey",
		};
		const color = colors[frm.doc.status] || "grey";
		frm.page.set_indicator(frm.doc.status, color);
	},

	add_status_buttons(frm) {
		if (frm.is_new() || !frm.doc.name) return;

		const transitions = {
			Draft: [
				{ label: __("Start Review"), target: "In Progress" },
				{ label: __("Cancel"), target: "Cancelled" },
			],
			Scheduled: [
				{ label: __("Start Review"), target: "In Progress" },
				{ label: __("Mark Missed"), target: "Missed" },
				{ label: __("Reschedule"), target: "Rescheduled" },
			],
			"In Progress": [
				{ label: __("Complete"), target: "Completed" },
				{ label: __("Reschedule"), target: "Rescheduled" },
			],
			Missed: [
				{ label: __("Reschedule"), target: "Rescheduled" },
			],
		};

		const available = transitions[frm.doc.status];
		if (!available) return;

		for (const t of available) {
			frm.add_custom_button(t.label, () => {
				frappe.confirm(
					__("Change review status to <b>{0}</b>?", [t.target]),
					() => {
						frm.set_value("status", t.target);
						frm.save();
					}
				);
			}, __("Status"));
		}
	},

	patient(frm) {
		if (!frm.doc.patient) return;
		if (frm.doc.enrollment) return;

		frappe.call({
			method: "alcura_diabetes_obesity_disease_mgmt.api.encounter_context.get_enrollment_for_patient",
			args: { patient: frm.doc.patient },
			callback(r) {
				if (r.message) {
					frm.set_value("enrollment", r.message.enrollment);
					if (r.message.care_plan) {
						frm.set_value("care_plan", r.message.care_plan);
					}
				}
			},
		});
	},
});
