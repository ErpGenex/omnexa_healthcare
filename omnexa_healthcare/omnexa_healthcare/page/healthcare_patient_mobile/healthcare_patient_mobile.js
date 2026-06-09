frappe.pages["healthcare-patient-mobile"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Patient Mobile"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const patient = frappe.ui.form.make_control({
		parent: $root,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), reqd: 1 },
		render_input: true,
	});
	patient.$wrapper.css({ maxWidth: "320px", marginBottom: "12px" });
	patient.refresh();
	page.set_primary_action(__("Load"), () => {
		frappe.call({
			method: "omnexa_healthcare.api.portal.patient_mobile_home",
			args: { patient: patient.get_value() },
			callback(r) {
				const d = r.message || {};
				$root.find(".pm-data").remove();
				const $box = $(`<div class="pm-data"></div>`);
				$box.append(`<h6>${__("Appointments")}</h6>`);
				(d.appointments || []).forEach((a) => $box.append(`<div class="small">${a.appointment_date} — ${a.status}</div>`));
				$box.append(`<h6 class="mt-2">${__("Lab Results")}</h6>`);
				(d.lab_results || []).forEach((l) => $box.append(`<div class="small">${l.report_title} ${l.abnormal_flag ? "⚠" : ""}</div>`));
				$root.append($box);
			},
		});
	});
};
