frappe.pages["healthcare-follow-up-plans"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Specialty Follow-up Plans"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const $filters = $(`<div class="row mb-3"></div>`).appendTo($root);
	const patient = frappe.ui.form.make_control({
		parent: $filters,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient") },
		render_input: true,
	});
	const specialty = frappe.ui.form.make_control({
		parent: $filters,
		df: { fieldtype: "Link", options: "Healthcare Specialty", label: __("Specialty") },
		render_input: true,
	});
	const $list = $(`<div id="hc-follow-up-list"></div>`).appendTo($root);
	const $specs = $(`<div class="mt-4"><h5>${__("Multi-visit specialties")}</h5><div id="hc-multi-visit-specs"></div></div>`).appendTo($root);

	function render_plans(rows) {
		if (!rows.length) {
			$list.html(`<p class="text-muted">${__("No follow-up plans for this patient.")}</p>`);
			return;
		}
		const html = [`<table class="table table-bordered table-sm"><thead><tr>
			<th>${__("Plan")}</th><th>${__("Specialty")}</th><th>${__("Type")}</th><th>${__("Progress")}</th><th>${__("Status")}</th>
		</tr></thead><tbody>`];
		rows.forEach((r) => {
			html.push(`<tr><td><a href="/app/healthcare-follow-up-plan/${encodeURIComponent(r.name)}">${frappe.utils.escape_html(r.plan_title)}</a></td>
				<td>${frappe.utils.escape_html(r.specialty_name || r.specialty)}</td>
				<td>${frappe.utils.escape_html(r.plan_type)}</td>
				<td>${r.progress_pct || 0}% (${r.visits_completed || 0}/${r.visits_total || 0})</td>
				<td>${frappe.utils.escape_html(r.status)}</td></tr>`);
		});
		html.push("</tbody></table>");
		$list.html(html.join(""));
	}

	function load_plans() {
		const p = patient.get_value();
		if (!p) return frappe.msgprint(__("Select a patient"));
		frappe.call({
			method: "omnexa_healthcare.api.follow_up_plan.get_patient_follow_up_plans",
			args: { patient: p, specialty: specialty.get_value() || null },
			callback(r) { render_plans(r.message || []); },
		});
	}

	page.set_primary_action(__("Load Plans"), load_plans);
	page.add_menu_item(__("New Follow-up Plan"), () => frappe.new_doc("Healthcare Follow Up Plan"));
	page.add_menu_item(__("Create from template"), () => {
		const p = patient.get_value();
		const s = specialty.get_value();
		if (!p || !s) return frappe.msgprint(__("Select patient and specialty"));
		frappe.call({
			method: "omnexa_healthcare.api.follow_up_plan.create_follow_up_plan",
			args: { patient: p, specialty: s },
			callback(r) {
				frappe.show_alert({ message: __("Plan created"), indicator: "green" });
				if (r.message?.name) frappe.set_route("Form", "Healthcare Follow Up Plan", r.message.name);
				load_plans();
			},
		});
	});

	frappe.call({
		method: "omnexa_healthcare.api.follow_up_plan.list_multi_visit_specialties",
		callback(r) {
			const rows = r.message || [];
			const html = [`<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Specialty")}</th><th>${__("Default plan")}</th><th>${__("Visits")}</th>
			</tr></thead><tbody>`];
			rows.forEach((row) => {
				html.push(`<tr><td>${frappe.utils.escape_html(row.specialty_name || row.module_name)}</td>
					<td>${frappe.utils.escape_html(row.default_plan_type || "")}</td>
					<td>${row.visit_count || 0}</td></tr>`);
			});
			html.push("</tbody></table>");
			$("#hc-multi-visit-specs").html(html.join(""));
		},
	});

	patient.refresh();
	specialty.refresh();
};
