frappe.pages["healthcare-patient-journey"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Patient Journey Wizard"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const patient = frappe.ui.form.make_control({
		parent: $root,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), reqd: 1 },
		render_input: true,
	});
	patient.$wrapper.css({ maxWidth: "360px" });
	const $steps = $(`<div class="mt-3" id="hc-journey-steps"></div>`).appendTo($root);

	page.set_primary_action(__("Load Journey"), () => {
		const p = patient.get_value();
		if (!p) return frappe.msgprint(__("Select a patient"));
		frappe.call({
			method: "omnexa_healthcare.api.patient_journey.get_patient_journey",
			args: { patient: p },
			callback(r) {
				const j = r.message || {};
				let html = `<h5>${__("Progress")}: ${j.progress_pct || 0}%</h5><ul class="list-group">` +
					(j.steps || []).map((s) => {
						const badge = s.state === "completed" ? "success" : s.state === "pending" ? "warning" : "secondary";
						return `<li class="list-group-item d-flex justify-content-between"><span>${frappe.utils.escape_html(s.label)}</span><span class="badge bg-${badge}">${frappe.utils.escape_html(s.state)}</span></li>`;
					}).join("") + "</ul>";
				if ((j.follow_up_plans || []).length) {
					html += `<h5 class="mt-3">${__("Multi-Visit Follow-up Plans")}</h5><ul class="list-group">` +
						j.follow_up_plans.map((p) =>
							`<li class="list-group-item d-flex justify-content-between">
								<span>${frappe.utils.escape_html(p.plan_title)} — ${frappe.utils.escape_html(p.specialty_name || "")}</span>
								<span class="badge bg-info">${p.progress_pct || 0}%</span></li>`
						).join("") + "</ul>";
				}
				$steps.html(html);
			},
		});
	});
	patient.refresh();
};
