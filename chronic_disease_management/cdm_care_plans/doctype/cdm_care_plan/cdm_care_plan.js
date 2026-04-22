frappe.ui.form.on("CDM Care Plan", {
	refresh(frm) {
		frm.events.set_status_indicator(frm);
		frm.events.add_status_buttons(frm);
		frm.events.add_goal_button(frm);
		frm.events.render_connections(frm);
	},

	set_status_indicator(frm) {
		const colors = {
			Draft: "orange",
			Active: "green",
			"Under Review": "blue",
			Completed: "darkgrey",
			Cancelled: "red",
		};
		const color = colors[frm.doc.status] || "grey";
		frm.page.set_indicator(frm.doc.status, color);
	},

	add_status_buttons(frm) {
		if (frm.is_new() || !frm.doc.name) return;

		const transitions = {
			Draft: [
				{ label: __("Activate"), target: "Active", icon: "play" },
				{ label: __("Cancel"), target: "Cancelled", icon: "close" },
			],
			Active: [
				{ label: __("Put Under Review"), target: "Under Review", icon: "edit" },
				{ label: __("Complete"), target: "Completed", icon: "check" },
				{ label: __("Cancel"), target: "Cancelled", icon: "close" },
			],
			"Under Review": [
				{ label: __("Re-activate"), target: "Active", icon: "play" },
				{ label: __("Complete"), target: "Completed", icon: "check" },
				{ label: __("Cancel"), target: "Cancelled", icon: "close" },
			],
		};

		const available = transitions[frm.doc.status];
		if (!available) return;

		for (const t of available) {
			frm.add_custom_button(t.label, () => {
				frappe.confirm(
					__("Change care plan status to <b>{0}</b>?", [t.target]),
					() => {
						frm.set_value("status", t.target);
						frm.save();
					}
				);
			}, __("Status"));
		}
	},

	add_goal_button(frm) {
		if (frm.is_new() || !frm.doc.name) return;
		if (["Completed", "Cancelled"].includes(frm.doc.status)) return;

		frm.add_custom_button(__("Add Goal"), () => {
			frappe.new_doc("Disease Goal", {
				care_plan: frm.doc.name,
				patient: frm.doc.patient,
			});
		}, __("Actions"));
	},

	render_connections(frm) {
		if (frm.is_new() || !frm.doc.name) return;

		frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Disease Review Sheet",
				filters: { care_plan: frm.doc.name },
			},
			callback(r) {
				if (!r || r.message === undefined) return;
				const count = r.message;
				const html = count > 0
					? `<a href="/app/disease-review-sheet?care_plan=${frm.doc.name}">${count} Review Sheet(s)</a>`
					: '<span class="text-muted">No review sheets linked yet.</span>';
				frm.fields_dict.connections_html.$wrapper.html(
					`<div class="mt-2">${html}</div>`
				);
			},
		});
	},
});
