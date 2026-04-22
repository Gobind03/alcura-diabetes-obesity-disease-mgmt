frappe.ui.form.on("Patient Encounter", {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.patient) return;

		frm.add_custom_button(__("Enroll in Disease Program"), () => {
			frm.events.cdm_launch_enrollment(frm);
		}, __("CDM"));

		frm.add_custom_button(__("Disease Review"), () => {
			frm.events.cdm_launch_review(frm);
		}, __("CDM"));

		frm.events.cdm_load_context_panel(frm);
	},

	// -----------------------------------------------------------------
	// Enrollment launch (Story 5)
	// -----------------------------------------------------------------

	cdm_launch_enrollment(frm) {
		frappe.call({
			method: "chronic_disease_management.api.enrollment.get_enrollment_context",
			args: {
				patient: frm.doc.patient,
				source_encounter: frm.doc.name,
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
			source_encounter: ctx.source_encounter || "",
		};
		if (ctx.practitioner) {
			route_opts.practitioner = ctx.practitioner;
			route_opts.practitioner_name = ctx.practitioner_name || "";
		}
		frappe.new_doc("Disease Enrollment", route_opts);
	},

	// -----------------------------------------------------------------
	// Disease Review launch (Story 8)
	// -----------------------------------------------------------------

	cdm_launch_review(frm) {
		frappe.call({
			method: "chronic_disease_management.api.encounter_context.create_review_from_encounter",
			args: { encounter: frm.doc.name },
			freeze: true,
			freeze_message: __("Loading review..."),
			callback(r) {
				if (r.message) {
					frappe.set_route("Form", "Disease Review Sheet", r.message);
				}
			},
			error() {
				frappe.msgprint({
					title: __("CDM"),
					message: __("Could not create a review sheet. The patient may not have an active enrollment."),
					indicator: "orange",
				});
			},
		});
	},

	// -----------------------------------------------------------------
	// CDM Context Panel (Story 9)
	// -----------------------------------------------------------------

	cdm_load_context_panel(frm) {
		frappe.call({
			method: "chronic_disease_management.api.encounter_context.get_disease_context",
			args: {
				patient: frm.doc.patient,
				encounter: frm.doc.name,
			},
			callback(r) {
				if (!r.message || !r.message.has_cdm_data) return;
				frm.events.cdm_render_panel(frm, r.message);
			},
		});
	},

	cdm_render_panel(frm, ctx) {
		const $wrapper = frm.dashboard.add_section("", __("Chronic Disease Management"));

		let html = '<div class="cdm-context-panel" style="padding: 8px 0;">';

		// Status badges
		html += '<div class="d-flex gap-2 mb-3 flex-wrap">';
		if (ctx.enrollment) {
			html += `<span class="badge badge-pill badge-primary">${ctx.enrollment.disease_type} — ${ctx.enrollment.program_status}</span>`;
		}
		if (ctx.care_plan) {
			html += `<span class="badge badge-pill badge-info">Care Plan: ${ctx.care_plan.status}</span>`;
		}
		if (ctx.pending_review) {
			html += `<span class="badge badge-pill badge-warning">Review: ${ctx.pending_review.review_type}</span>`;
		}
		html += "</div>";

		// Goals summary
		if (ctx.goals && ctx.goals.length) {
			html += '<div class="mb-3"><strong>' + __("Goals") + "</strong>";
			html += '<table class="table table-sm table-bordered mt-1" style="font-size: 12px;">';
			html += "<thead><tr><th>Metric</th><th>Target</th><th>Current</th><th>Status</th></tr></thead><tbody>";
			for (const g of ctx.goals) {
				const target_display = g.target_value || "";
				const current_display = g.current_value || "\u2014";
				const status_color = {
					"Not Started": "text-muted",
					"In Progress": "text-info",
					"Achieved": "text-success",
					"Partially Met": "text-warning",
					"Not Met": "text-danger",
				}[g.status] || "text-muted";
				html += `<tr><td>${g.goal_metric}</td><td>${target_display}</td><td>${current_display}</td>`;
				html += `<td class="${status_color}">${g.status}</td></tr>`;
			}
			html += "</tbody></table></div>";
		}

		// Recent data row
		html += '<div class="row mb-3">';

		if (ctx.recent_vitals) {
			const v = ctx.recent_vitals;
			html += '<div class="col-sm-4"><strong>' + __("Recent Vitals") + "</strong>";
			html += `<div class="text-muted" style="font-size: 11px;">${v.signs_date || ""}</div>`;
			html += '<ul class="list-unstyled mb-0" style="font-size: 12px;">';
			if (v.weight) html += `<li>Weight: ${v.weight} kg</li>`;
			if (v.bmi) html += `<li>BMI: ${v.bmi}</li>`;
			if (v.bp_systolic) html += `<li>BP: ${v.bp_systolic}/${v.bp_diastolic} mmHg</li>`;
			html += "</ul></div>";
		}

		if (ctx.recent_labs) {
			const l = ctx.recent_labs;
			html += '<div class="col-sm-4"><strong>' + __("Recent Labs") + "</strong>";
			html += '<ul class="list-unstyled mb-0" style="font-size: 12px;">';
			if (l.hba1c) html += `<li>HbA1c: ${l.hba1c}% <span class="text-muted">(${l.hba1c_date || ""})</span></li>`;
			if (l.fbs) html += `<li>FBS: ${l.fbs} mg/dL <span class="text-muted">(${l.fbs_date || ""})</span></li>`;
			html += "</ul></div>";
		}

		if (ctx.trends && Object.keys(ctx.trends).length) {
			html += '<div class="col-sm-4"><strong>' + __("Trends") + "</strong>";
			html += '<ul class="list-unstyled mb-0" style="font-size: 12px;">';
			const trend_icons = { decreasing: "\u2193", increasing: "\u2191", stable: "\u2192", improving: "\u2193", worsening: "\u2191" };
			if (ctx.trends.weight_trend) {
				html += `<li>Weight: ${trend_icons[ctx.trends.weight_trend] || ""} ${ctx.trends.weight_trend}</li>`;
			}
			if (ctx.trends.hba1c_trend) {
				html += `<li>HbA1c: ${trend_icons[ctx.trends.hba1c_trend] || ""} ${ctx.trends.hba1c_trend}</li>`;
			}
			html += "</ul></div>";
		}

		html += "</div>";

		// Medications
		if (ctx.medications && ctx.medications.length) {
			html += '<div class="mb-3"><strong>' + __("Active Medications") + "</strong>";
			html += '<div style="font-size: 12px;">';
			html += ctx.medications.map((m) => m.medication).filter(Boolean).join(", ") || __("None");
			html += "</div></div>";
		}

		// Care gaps
		if (ctx.care_gaps && ctx.care_gaps.length) {
			html += `<div class="mb-3"><strong>${__("Care Gaps")}</strong>: ${ctx.care_gaps.length} open</div>`;
		}

		// Action buttons
		html += '<div class="d-flex gap-2 flex-wrap">';
		if (ctx.care_plan) {
			html += `<button class="btn btn-xs btn-default cdm-action" data-action="open-care-plan" data-name="${ctx.care_plan.name}">${__("Open Care Plan")}</button>`;
		}
		if (ctx.pending_review) {
			html += `<button class="btn btn-xs btn-default cdm-action" data-action="open-review" data-name="${ctx.pending_review.name}">${__("Open Review")}</button>`;
		} else {
			html += `<button class="btn btn-xs btn-primary cdm-action" data-action="create-review">${__("Create Review")}</button>`;
		}
		if (ctx.enrollment) {
			html += `<button class="btn btn-xs btn-default cdm-action" data-action="open-enrollment" data-name="${ctx.enrollment.name}">${__("Open Enrollment")}</button>`;
		}
		html += "</div>";

		html += "</div>";

		$wrapper.html(html);

		$wrapper.find(".cdm-action").on("click", function () {
			const action = $(this).data("action");
			const name = $(this).data("name");
			if (action === "open-care-plan") {
				frappe.set_route("Form", "CDM Care Plan", name);
			} else if (action === "open-review") {
				frappe.set_route("Form", "Disease Review Sheet", name);
			} else if (action === "create-review") {
				frm.events.cdm_launch_review(frm);
			} else if (action === "open-enrollment") {
				frappe.set_route("Form", "Disease Enrollment", name);
			}
		});
	},
});
