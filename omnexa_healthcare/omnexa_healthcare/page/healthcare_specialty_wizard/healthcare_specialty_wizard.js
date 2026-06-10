frappe.pages["healthcare-specialty-wizard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Specialty Onboarding Wizard"), single_column: true });
	const $body = $(page.body);
	$body.html(`<p class="text-muted">${__("Create a new specialty module without code — configure workflows in JSON.")}</p>`);

	frappe.call({ method: "omnexa_healthcare.specialty_engine.list_specialty_modules", callback(r) {
		const rows = r.message || [];
		const html = [`<table class="table table-bordered"><thead><tr><th>${__("Module")}</th><th>${__("Specialty")}</th><th>${__("Chart")}</th></tr></thead><tbody>`];
		rows.forEach((m) => html.push(`<tr><td>${frappe.utils.escape_html(m.module_name)}</td><td>${frappe.utils.escape_html(m.specialty)}</td><td>${frappe.utils.escape_html(m.chart_type)}</td></tr>`));
		html.push("</tbody></table>");
		$body.append(html.join(""));
	}});

	page.set_primary_action(__("New Specialty Module"), () => {
		frappe.new_doc("Healthcare Specialty Module");
	});
	page.add_menu_item(__("Seed 15 Default Specialties"), () => {
		frappe.call({
			method: "omnexa_healthcare.specialty_engine.seed_default_specialty_modules",
			callback() { frappe.show_alert({ message: __("Specialties seeded"), indicator: "green" }); frappe.set_route("healthcare-specialty-wizard"); },
		});
	});
};
