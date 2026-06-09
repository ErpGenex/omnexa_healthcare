frappe.ui.form.on("Healthcare Appointment", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus === 2) return;
		if (!frm.doc.service_charge && frm.doc.patient) {
			frm.add_custom_button(__("Create Service Charge"), () => {
				frappe.call({
					method: "omnexa_healthcare.api.billing_automation.create_service_charge_from_appointment",
					args: { appointment: frm.doc.name },
					callback(r) {
						if (r.message?.name) {
							frappe.show_alert({ message: __("Service Charge {0} created", [r.message.name]), indicator: "green" });
							frm.reload_doc();
						}
					},
				});
			});
		}
	},
});
