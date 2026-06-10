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
				if (c.wado_rs_stream_url || c.wado_url) {
					const stream = c.wado_rs_stream_url ? `<p class="small">${__("WADO-RS Stream")}: <code>${frappe.utils.escape_html(c.wado_rs_stream_url)}</code></p>` : "";
					const url = c.wado_url || c.wado_rs_stream_url;
					$frame.html(
						`${stream}<p>${__("DICOMweb URL")}: <a href="${frappe.utils.escape_html(url)}" target="_blank">${__(
							"Open in PACS viewer"
						)}</a></p><iframe src="${frappe.utils.escape_html(url)}" style="width:100%;height:500px;border:0"></iframe>`
					);
				} else {
					$frame.html(`<p class="text-muted">${__("Configure PACS WADO URL on Healthcare Settings or report.")}</p>`);
				}
			},
		});
	});
};
