frappe.ui.form.on("Healthcare Service Charge", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status !== "Draft" || frm.doc.sales_invoice) {
			return;
		}
		frm.add_custom_button(__("Create Sales Invoice"), () => {
			frappe.call({
				method: "omnexa_healthcare.api.billing.create_sales_invoice_from_service_charge",
				args: { service_charge: frm.doc.name },
				freeze: true,
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Sales Invoice created"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		});
	},
});
