frappe.ui.form.on("Healthcare Branch Website", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__("Copy site link"), () => copy_site_link(frm, "home"), __("Share"));
		frm.add_custom_button(__("Copy booking link"), () => copy_site_link(frm, "booking"), __("Share"));
		frm.add_custom_button(__("Share site"), () => share_site_link(frm), __("Share"));

		if (frm.doc.is_enabled && frm.doc.site_slug) {
			const preview = `/hospital?site=${encodeURIComponent(frm.doc.site_slug)}`;
			frm.dashboard.add_comment(
				__("Public URL: {0}", [`<a href="${preview}" target="_blank">${preview}</a>`]),
				"blue",
				true
			);
		}
	},
});

function fetch_site_urls(frm, callback) {
	frappe.call({
		method: "omnexa_healthcare.api.public_hospital_site.get_site_urls",
		args: { branch: frm.doc.branch },
		callback(r) {
			callback(r.message || {});
		},
	});
}

function copy_site_link(frm, key) {
	fetch_site_urls(frm, (msg) => {
		const url = (msg.urls && msg.urls[key]) || msg.public_url;
		if (!url) {
			frappe.msgprint(__("Could not resolve public URL."));
			return;
		}
		frappe.utils.copy_to_clipboard(url);
		frappe.show_alert({ message: __("Link copied to clipboard"), indicator: "green" });
	});
}

function share_site_link(frm) {
	fetch_site_urls(frm, (msg) => {
		const url = msg.public_url;
		const title = frm.doc.hospital_name_ar || frm.doc.hospital_name_en || frm.doc.branch;
		if (navigator.share) {
			navigator.share({ title, text: frm.doc.tagline_ar || frm.doc.tagline_en || title, url }).catch(() => {
				frappe.utils.copy_to_clipboard(url);
				frappe.show_alert({ message: __("Link copied to clipboard"), indicator: "green" });
			});
			return;
		}
		frappe.utils.copy_to_clipboard(url);
		frappe.show_alert({ message: __("Link copied to clipboard"), indicator: "green" });
	});
}
