frappe.ui.form.on("Patient Appointment", {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.patient) return;

		frm.add_custom_button(__("Enroll in Disease Program"), () => {
			frm.events.cdm_launch_enrollment(frm);
		}, __("CDM"));
	},

	cdm_launch_enrollment(frm) {
		frappe.call({
			method: "alcura_diabetes_obesity_disease_mgmt.api.enrollment.get_enrollment_context",
			args: {
				patient: frm.doc.patient,
				source_appointment: frm.doc.name,
			},
			callback(r) {
				if (!r.message) return;
				const ctx = r.message;

				if (ctx.existing_enrollments && ctx.existing_enrollments.length) {
					const rows = ctx.existing_enrollments.map(
						(e) => `<li><strong>${e.disease_type}</strong> — ${e.program_status} (${e.name})</li>`
					).join("");
					frappe.confirm(
						__("This patient already has active enrollments:") +
						`<ul class="mt-2">${rows}</ul>` +
						__("Do you still want to create a new enrollment?"),
						() => frm.events.cdm_open_enrollment_form(ctx)
					);
				} else {
					frm.events.cdm_open_enrollment_form(ctx);
				}
			},
		});
	},

	cdm_open_enrollment_form(ctx) {
		const route_opts = {
			doctype: "Disease Enrollment",
			patient: ctx.patient,
			patient_name: ctx.patient_name || "",
			patient_sex: ctx.patient_sex || "",
			patient_age: ctx.patient_age || "",
			source_appointment: ctx.source_appointment || "",
		};
		if (ctx.practitioner) {
			route_opts.practitioner = ctx.practitioner;
			route_opts.practitioner_name = ctx.practitioner_name || "";
		}
		frappe.new_doc("Disease Enrollment", route_opts);
	},
});
