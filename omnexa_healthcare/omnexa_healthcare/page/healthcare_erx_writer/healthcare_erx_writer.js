frappe.pages["healthcare-erx-writer"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("ePrescription Writer"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const $filters = $(`<div class="row mb-3"></div>`).appendTo($root);
	const patient = frappe.ui.form.make_control({ parent: $filters, df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), reqd: 1 }, render_input: true });
	const practitioner = frappe.ui.form.make_control({ parent: $filters, df: { fieldtype: "Link", options: "Healthcare Practitioner", label: __("Prescriber"), reqd: 1 }, render_input: true });
	const diagnosis = frappe.ui.form.make_control({ parent: $filters, df: { fieldtype: "Data", label: __("Diagnosis"), reqd: 1 }, render_input: true });
	const $drugSearch = $(`<div class="row mb-2"><div class="col-md-8" id="hc-erx-drug"></div><div class="col-md-4 pt-4"><button class="btn btn-sm btn-secondary" id="hc-erx-add">${__("Add line")}</button></div></div>`).appendTo($root);
	const drugQuery = frappe.ui.form.make_control({ parent: $("#hc-erx-drug"), df: { fieldtype: "Data", label: __("Smart drug search") }, render_input: true });
	const $lines = $(`<table class="table table-sm table-bordered"><thead><tr><th>${__("Drug")}</th><th>${__("Dose")}</th><th>${__("Frequency")}</th><th></th></tr></thead><tbody id="hc-erx-lines"></tbody></table>`).appendTo($root);
	const $cds = $(`<div id="hc-erx-cds" class="alert alert-warning mt-3" style="display:none"></div>`).appendTo($root);
	const lines = [];

	function renderLines() {
		const html = lines.map((l, i) => `<tr><td>${frappe.utils.escape_html(l.drug_name)}</td><td>${frappe.utils.escape_html(l.dose || "")}</td><td>${frappe.utils.escape_html(l.frequency || "")}</td><td><a href="#" data-i="${i}">${__("Remove")}</a></td></tr>`).join("");
		$("#hc-erx-lines").html(html || `<tr><td colspan="4" class="text-muted">${__("No medications")}</td></tr>`);
	}
	$lines.on("click", "a", (e) => { e.preventDefault(); lines.splice($(e.target).data("i"), 1); renderLines(); });

	$("#hc-erx-add").on("click", () => {
		const q = drugQuery.get_value();
		if (!q) return frappe.msgprint(__("Enter drug name or search term"));
		frappe.call({
			method: "omnexa_healthcare.api.erx.search_drugs",
			args: { query: q, limit: 1 },
			callback(r) {
				const row = (r.message || [])[0] || { drug_name: q };
				lines.push({ drug_name: row.drug_name || q, rxnorm_code: row.rxnorm_cui || row.rxnorm_code, dose: row.strength || "", frequency: "OD", quantity: 1, route: "Oral" });
				renderLines();
			},
		});
	});

	function previewCds() {
		const p = patient.get_value();
		if (!p || !lines.length) return;
		frappe.call({
			method: "omnexa_healthcare.api.cds.evaluate_erx_cds",
			args: { patient: p, items: lines },
			callback(r) {
				const alerts = r.message || [];
				if (!alerts.length) { $cds.hide(); return; }
				$cds.show().html(`<strong>${__("CDS Alerts")}</strong><ul>${alerts.map((a) => `<li>[${a.severity}] ${frappe.utils.escape_html(a.message)}</li>`).join("")}</ul>`);
			},
		});
	}

	page.set_primary_action(__("Create & Sign"), () => {
		const p = patient.get_value(), pr = practitioner.get_value(), dx = diagnosis.get_value();
		if (!p || !pr || !dx || !lines.length) return frappe.msgprint(__("Complete patient, prescriber, diagnosis and add medications"));
		frappe.call({
			method: "omnexa_healthcare.api.erx.create_medication_request",
			args: { patient: p, practitioner: pr, diagnosis: dx, items: lines, company: frappe.defaults.get_default("company"), branch: frappe.defaults.get_user_default("Branch") },
			callback(r) {
				frappe.call({
					method: "omnexa_healthcare.api.erx.sign_medication_request",
					args: { name: r.message.name },
					callback(s) {
						frappe.show_alert({ message: __("Prescription signed"), indicator: "green" });
						frappe.set_route("Form", "Healthcare Medication Request", s.message.name);
					},
				});
			},
		});
	});
	page.add_menu_item(__("Preview CDS"), previewCds);
	renderLines();
};
