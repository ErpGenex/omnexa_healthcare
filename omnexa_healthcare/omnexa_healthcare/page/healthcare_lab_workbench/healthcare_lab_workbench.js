frappe.pages["healthcare-lab-workbench"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Lab Workbench"), single_column: true });
	const branch = frappe.ui.form.make_control({ parent: $(page.body), df: { fieldtype: "Link", options: "Branch", label: __("Branch"), reqd: 1 }, render_input: true });
	page.set_primary_action(__("Load"), () => {
		frappe.call({ method: "omnexa_healthcare.api.lab_lis.api_get_lab_worklist", args: { branch: branch.get_value() }, callback: (r) => {
			const rows = (r.message || []).map((x) => `<tr><td>${x.name}</td><td>${x.patient_display}</td><td>${x.status}</td><td>${x.specimen_id || ""}</td></tr>`).join("");
			$(page.body).find(".lab-grid").remove();
			$(page.body).append(`<div class="lab-grid"><table class="table table-bordered"><thead><tr><th>Sample</th><th>Patient</th><th>Status</th><th>Barcode</th></tr></thead><tbody>${rows}</tbody></table></div>`);
		}});
	});
};
