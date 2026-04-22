frappe.ui.form.on("Disease Goal", {
	refresh(frm) {
		frm.events.set_status_indicator(frm);
		frm.events.add_revise_button(frm);
	},

	set_status_indicator(frm) {
		const colors = {
			"Not Started": "orange",
			"In Progress": "blue",
			Achieved: "green",
			"Partially Met": "yellow",
			"Not Met": "red",
			Revised: "grey",
		};
		const color = colors[frm.doc.status] || "grey";
		frm.page.set_indicator(frm.doc.status, color);
	},

	add_revise_button(frm) {
		if (frm.is_new() || !frm.doc.name) return;
		if (frm.doc.status === "Revised") return;

		frm.add_custom_button(__("Revise Goal"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Revise Goal"),
				fields: [
					{
						fieldname: "new_target_value",
						fieldtype: "Data",
						label: __("New Target Value"),
						default: frm.doc.target_value,
					},
					{
						fieldname: "new_rationale",
						fieldtype: "Small Text",
						label: __("Rationale for Revision"),
					},
				],
				primary_action_label: __("Revise"),
				primary_action(values) {
					frappe.call({
						method: "revise_goal",
						doc: frm.doc,
						args: {
							new_target_value: values.new_target_value,
							new_rationale: values.new_rationale,
						},
						callback(r) {
							if (r.message) {
								d.hide();
								frappe.set_route("Form", "Disease Goal", r.message);
								frappe.show_alert({
									message: __("Goal revised successfully"),
									indicator: "green",
								});
							}
						},
					});
				},
			});
			d.show();
		}, __("Actions"));
	},

	goal_metric(frm) {
		const unit_map = {
			HbA1c: "%",
			"Fasting Glucose": "mg/dL",
			"Post-Prandial Glucose": "mg/dL",
			TIR: "%",
			Weight: "kg",
			BMI: "kg/m²",
			"Waist Circumference": "cm",
			"BP Systolic": "mmHg",
			"BP Diastolic": "mmHg",
			"Activity Minutes/Week": "min/week",
			"Diet Adherence Score": "%",
		};
		const unit = unit_map[frm.doc.goal_metric];
		if (unit) {
			frm.set_value("target_unit", unit);
		}
	},
});
