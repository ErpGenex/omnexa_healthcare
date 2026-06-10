frappe.ui.form.on("Healthcare Patient", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Medical file / الملف الطبي"), () => {
			frappe.set_route("page", "healthcare-patient-chart", { patient: frm.doc.name });
		});
		frm.add_custom_button(__("FHIR Patient (IPS)"), () => {
			frappe.call({
				method: "omnexa_healthcare.api.fhir_export.get_fhir_patient_summary_ips_bundle",
				args: { patient: frm.doc.name },
				callback(r) {
					frappe.msgprint({
						title: __("International Patient Summary"),
						message: `<pre style="max-height:420px;overflow:auto">${frappe.utils.escape_html(
							JSON.stringify(r.message || {}, null, 2)
						)}</pre>`,
						wide: true,
					});
				},
			});
		});
	},
});
