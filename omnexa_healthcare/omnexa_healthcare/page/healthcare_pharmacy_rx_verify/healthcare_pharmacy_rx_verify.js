frappe.pages["healthcare-pharmacy-rx-verify"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Pharmacy Rx Verify"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const qr = frappe.ui.form.make_control({ parent: $root, df: { fieldtype: "Data", label: __("QR token"), reqd: 1 }, render_input: true });
	const warehouse = frappe.ui.form.make_control({ parent: $root, df: { fieldtype: "Link", options: "Warehouse", label: __("Warehouse"), reqd: 1 }, render_input: true });
	const $result = $(`<div id="hc-rx-verify-result" class="mt-3"></div>`).appendTo($root);

	page.set_primary_action(__("Verify QR"), () => {
		frappe.call({
			method: "omnexa_healthcare.api.erx.verify_qr_token",
			args: { qr_token: qr.get_value() },
			callback(r) {
				const d = r.message || {};
				$result.html(`<div class="alert alert-success"><strong>${__("Valid prescription")}</strong> ${d.medication_request} · ${d.patient} · ${d.status}</div>`);
			},
		});
	});
	page.add_menu_item(__("Verify & dispense"), () => {
		frappe.call({
			method: "omnexa_healthcare.api.erx.verify_qr_token",
			args: { qr_token: qr.get_value() },
			callback(r) {
				frappe.call({
					method: "omnexa_healthcare.api.erx.pharmacy_verify_and_dispense",
					args: { medication_request: r.message.medication_request, warehouse: warehouse.get_value() },
					callback() { frappe.show_alert({ message: __("Dispensed"), indicator: "green" }); },
				});
			},
		});
	});
};
