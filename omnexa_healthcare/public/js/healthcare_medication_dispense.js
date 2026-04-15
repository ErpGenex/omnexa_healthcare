frappe.ui.form.on("Healthcare Medication Dispense", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status !== "draft" || frm.doc.stock_entry) {
			return;
		}
		if (!frm.doc.warehouse) {
			return;
		}
		frm.add_custom_button(__("Issue stock (Stock Entry)"), () => {
			frappe.call({
				method: "omnexa_healthcare.api.dispensing.create_stock_entry_from_medication_dispense",
				args: { medication_dispense: frm.doc.name },
				freeze: true,
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({ message: __("Stock Entry created"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		});
	},
});
