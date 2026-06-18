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
	const route = frappe.get_route();
	if (route.length > 1 && route[1]) {
		report.set_value(route[1]);
	}
	const $frame = $(`<div class="border mt-3" style="min-height:400px;padding:12px;background:#0a0a12;border-radius:8px"></div>`).appendTo($root);

	function isImageUrl(url) {
		return /\.(svg|png|jpe?g|gif|webp)(\?|$)/i.test(url || "");
	}

	function showStudy(c) {
		const url = c.wado_url || c.wado_rs_stream_url || "";
		if (!url) {
			$frame.html(`<p class="text-muted">${__("Configure PACS WADO URL on Healthcare Settings or report.")}</p>`);
			return;
		}
		if (isImageUrl(url)) {
			$frame.html(
				`<p class="small text-muted">${__("Demo study preview")}</p>
				<img src="${frappe.utils.escape_html(url)}" alt="${__("Radiology study")}" style="width:100%;max-height:560px;object-fit:contain;border-radius:8px" />
				<p class="small mt-2"><a href="${frappe.utils.escape_html(url)}" target="_blank">${__("Open image")}</a></p>`
			);
			return;
		}
		const stream = c.wado_rs_stream_url
			? `<p class="small">${__("WADO-RS Stream")}: <code>${frappe.utils.escape_html(c.wado_rs_stream_url)}</code></p>`
			: "";
		$frame.html(
			`${stream}<p>${__("DICOMweb URL")}: <a href="${frappe.utils.escape_html(url)}" target="_blank">${__(
				"Open in PACS viewer"
			)}</a></p><iframe src="${frappe.utils.escape_html(url)}" style="width:100%;height:500px;border:0"></iframe>`
		);
	}

	page.set_primary_action(__("Open Study"), () => {
		frappe.call({
			method: "omnexa_healthcare.api.radiology.api_get_dicom_viewer_config",
			args: { diagnostic_report: report.get_value() },
			callback(r) {
				showStudy(r.message || {});
			},
		});
	});

	if (report.get_value()) {
		page.btn_primary.trigger("click");
	}
};
