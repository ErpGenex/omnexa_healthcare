frappe.pages["healthcare-physician-mobile"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Physician Mobile"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	page.set_primary_action(__("Refresh"), () => load());
	function load() {
		frappe.call({
			method: "omnexa_healthcare.api.physician_app.api_physician_home",
			callback(r) {
				const d = r.message || {};
				$root.html(`<h5>${__("Today's Appointments")}</h5>`);
				const appts = d.appointments_today || [];
				if (!appts.length) $root.append(`<p class="text-muted">${__("No appointments today.")}</p>`);
				else {
					const $t = $(`<ul class="list-unstyled"></ul>`);
					appts.forEach((a) => $t.append(`<li>${frappe.utils.escape_html(a.patient)} — ${a.status}</li>`));
					$root.append($t);
				}
				$root.append(`<h5 class="mt-3">${__("In Basket")}</h5>`);
				const ib = d.in_basket || [];
				if (!ib.length) $root.append(`<p class="text-muted">${__("Empty")}</p>`);
				else ib.forEach((i) => $root.append(`<div class="small border-bottom py-1">${frappe.utils.escape_html(i.subject)}</div>`));
			},
		});
	}
	load();
};
