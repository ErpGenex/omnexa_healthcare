frappe.pages["healthcare-nursing-portal"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Nursing Portal"),
		single_column: true,
	});
	const $body = $(page.body);
	$body.append(`<p class="text-muted">${__("Ward tasks, eMAR shortcuts, incident reports, and shift handover.")}</p>`);
	const $grid = $(`<div class="row" style="margin-top:16px"></div>`).appendTo($body);
	const links = [
		{ route: "List/Healthcare Nursing Incident Report", label: __("Incident Reports"), icon: "fa-warning" },
		{ route: "List/Healthcare Nursing Shift Handover", label: __("Shift Handover"), icon: "fa-exchange" },
		{ route: "List/Healthcare Medication Administration Record", label: __("eMAR"), icon: "fa-medkit" },
		{ route: "List/Healthcare Nursing Care Plan", label: __("Care Plans"), icon: "fa-heartbeat" },
		{ route: "healthcare-icu-board", label: __("ICU Board"), icon: "fa-hospital-o" },
	];
	links.forEach((link) => {
		const $col = $(`<div class="col-md-4" style="margin-bottom:12px"></div>`).appendTo($grid);
		const $card = $(`<div class="card clickable" style="padding:16px;cursor:pointer"></div>`).appendTo($col);
		$card.html(`<i class="fa ${link.icon}"></i> <strong>${link.label}</strong>`);
		$card.on("click", () => {
			if (link.route.startsWith("List/")) frappe.set_route(link.route);
			else frappe.set_route(link.route);
		});
	});
	page.set_primary_action(__("New Incident Report"), () => frappe.new_doc("Healthcare Nursing Incident Report"));
	page.set_secondary_action(__("New Handover"), () => frappe.new_doc("Healthcare Nursing Shift Handover"));
};
