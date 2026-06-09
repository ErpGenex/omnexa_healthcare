frappe.pages["healthcare-dicom-viewer"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("DICOM Viewer"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const report = frappe.ui.form.make_control({
		parent: $root,
		df: { fieldtype: "Link", options: "Healthcare Diagnostic Report", label: __("Radiology Report"), reqd: 1 },
		render_input: true,
	});
	report.$wrapper.css({ maxWidth: "360px" });
	report.refresh();
	const $frame = $(`<div class="border mt-3" style="min-height:400px"></div>`).appendTo($root);
	page.set_primary_action(__("Open Study"), () => {
		frappe.call({
			method: "omnexa_healthcare.api.radiology.api_get_dicom_viewer_config",
			args: { diagnostic_report: report.get_value() },
			callback(r) {
				const c = r.message || {};
				if (c.wado_url) {
					$frame.html(
						`<p>${__("DICOMweb URL")}: <a href="${frappe.utils.escape_html(c.wado_url)}" target="_blank">${__(
							"Open in PACS viewer"
						)}</a></p><iframe src="${frappe.utils.escape_html(c.wado_url)}" style="width:100%;height:500px;border:0"></iframe>`
					);
				} else {
					$frame.html(`<p class="text-muted">${__("Configure PACS WADO URL on Healthcare Settings or report.")}</p>`);
				}
			},
		});
	});
};
