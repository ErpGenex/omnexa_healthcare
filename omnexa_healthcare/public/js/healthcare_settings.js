frappe.ui.form.on("Healthcare Settings", {
	refresh(frm) {
		if (!frm.doc.public_website_default_branch) {
			return;
		}
		frm.add_custom_button(__("Copy public site link"), () => {
			frappe.call({
				method: "omnexa_healthcare.api.public_hospital_site.get_site_urls",
				args: { branch: frm.doc.public_website_default_branch },
				callback(r) {
					const url = (r.message || {}).public_url;
					if (!url) {
						frappe.msgprint(__("Configure Healthcare Branch Website for this branch first."));
						return;
					}
					frappe.utils.copy_to_clipboard(url);
					frappe.show_alert({ message: __("Link copied to clipboard"), indicator: "green" });
				},
			});
		}, __("Website"));
		frm.add_custom_button(__("Open Branch Website settings"), () => {
			frappe.set_route("List", "Healthcare Branch Website", {
				branch: frm.doc.public_website_default_branch,
			});
		}, __("Website"));
	},
});
