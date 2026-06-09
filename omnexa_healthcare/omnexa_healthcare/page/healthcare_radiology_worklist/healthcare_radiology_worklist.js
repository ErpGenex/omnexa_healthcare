frappe.pages["healthcare-radiology-worklist"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Radiology Worklist"), single_column: true });
	const branch = frappe.ui.form.make_control({ parent: $(page.body), df: { fieldtype: "Link", options: "Branch", label: __("Branch"), reqd: 1 }, render_input: true });
	page.set_primary_action(__("Load"), () => {
		frappe.call({ method: "omnexa_healthcare.api.radiology.api_get_radiology_worklist", args: { branch: branch.get_value() }, callback: (r) => {
			const rows = (r.message || []).map((x) => `<tr><td>${x.name}</td><td>${x.patient_display}</td><td>${x.request_title}</td><td>${x.priority}</td><td>${x.status}</td></tr>`).join("");
			$(page.body).find(".rad-grid").remove();
			$(page.body).append(`<div class="rad-grid"><table class="table table-bordered"><thead><tr><th>Order</th><th>Patient</th><th>Study</th><th>Priority</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table></div>`);
		}});
	});
};
