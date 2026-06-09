frappe.pages["healthcare-executive-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Healthcare Executive Dashboard"), single_column: true });
	frappe.call({ method: "omnexa_healthcare.healthcare_compliance.get_healthcare_compliance_score", callback: (r) => {
		const s = r.message || {};
		$(page.body).html(`<div class="row"><div class="col-sm-4"><div class="card"><div class="card-body"><h4>${__("Compliance Score")}</h4><h2>${s.weighted_score || 0} / ${s.max_score || 5}</h2></div></div></div></div>`);
	}});
};
