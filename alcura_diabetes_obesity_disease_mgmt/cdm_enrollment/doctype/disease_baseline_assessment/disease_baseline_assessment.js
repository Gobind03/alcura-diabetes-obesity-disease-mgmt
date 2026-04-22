frappe.ui.form.on("Disease Baseline Assessment", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Refresh from Healthcare Data"), () => {
				frappe.confirm(
					__("This will re-fetch vitals, labs, and medications from the patient's healthcare records. Continue?"),
					() => {
						frappe.call({
							method: "alcura_diabetes_obesity_disease_mgmt.api.enrollment.refresh_baseline",
							args: {
								baseline: frm.doc.name,
								overwrite_manual: false,
							},
							callback(r) {
								if (r.message) {
									const msg = r.message;
									frappe.msgprint(
										__("Refreshed {0} field(s). {1} care gap(s) identified.", [
											msg.fields_refreshed ? msg.fields_refreshed.length : 0,
											msg.care_gaps_found || 0,
										])
									);
									frm.reload_doc();
								}
							},
						});
					}
				);
			});
		}

		frm.events.render_care_gap_summary(frm);
	},

	height_cm(frm) {
		frm.events.compute_bmi(frm);
	},

	weight_kg(frm) {
		frm.events.compute_bmi(frm);
	},

	compute_bmi(frm) {
		const height = frm.doc.height_cm;
		const weight = frm.doc.weight_kg;
		if (height && weight && height > 0) {
			const height_m = height / 100;
			const bmi = weight / (height_m * height_m);
			frm.set_value("bmi", flt(bmi, 1));

			let cls = "";
			if (bmi < 25) cls = "Normal";
			else if (bmi < 30) cls = "Overweight";
			else if (bmi < 35) cls = "Class I Obesity";
			else if (bmi < 40) cls = "Class II Obesity";
			else cls = "Class III Obesity";
			frm.set_value("obesity_class", cls);
		}
	},

	enrollment(frm) {
		if (!frm.doc.enrollment) return;
		frappe.db.get_value("Disease Enrollment", frm.doc.enrollment, [
			"patient", "patient_name", "disease_type", "source_encounter",
		]).then((r) => {
			if (!r.message) return;
			const data = r.message;
			frm.set_value("patient", data.patient || "");
			frm.set_value("patient_name", data.patient_name || "");
			frm.set_value("disease_type", data.disease_type || "");
			if (data.source_encounter) {
				frm.set_value("source_encounter", data.source_encounter);
			}
		});
	},

	render_care_gap_summary(frm) {
		if (!frm.doc.care_gaps || !frm.doc.care_gaps.length) return;

		const open_gaps = frm.doc.care_gaps.filter((g) => g.status === "Open");
		if (open_gaps.length > 0) {
			const high = open_gaps.filter((g) => g.priority === "High").length;
			const medium = open_gaps.filter((g) => g.priority === "Medium").length;
			const low = open_gaps.filter((g) => g.priority === "Low").length;
			const parts = [];
			if (high) parts.push(`<span class="text-danger">${high} High</span>`);
			if (medium) parts.push(`<span class="text-warning">${medium} Medium</span>`);
			if (low) parts.push(`<span class="text-muted">${low} Low</span>`);

			frm.dashboard.set_headline(
				__("Open Care Gaps: ") + parts.join(", ")
			);
		}
	},
});
