frappe.pages["healthcare-patient-consumer"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("My Health"),
		single_column: true,
	});
	const $body = $(page.body);
	const state = { patient: null, session_token: null };
	const $hero = $(`<div class="patient-consumer-hero" style="padding:16px;background:linear-gradient(135deg,#0d6efd22,#19875422);border-radius:12px;margin-bottom:16px"></div>`).appendTo($body);
	$hero.html(`<h4>${__("Consumer patient experience")}</h4><p class="text-muted">${__("OTP login, appointments, lab results, imaging, payments, and telehealth.")}</p>`);
	const $tabs = $(`<ul class="nav nav-tabs" role="tablist"></ul>`).appendTo($body);
	const $content = $(`<div class="tab-content" style="margin-top:12px"></div>`).appendTo($body);
	const tabs = [
		{ id: "otp", label: __("OTP Login") },
		{ id: "appointments", label: __("Appointments") },
		{ id: "labs", label: __("Lab Results") },
		{ id: "imaging", label: __("Imaging") },
		{ id: "pay", label: __("Pay") },
		{ id: "tele", label: __("Telehealth") },
		{ id: "family", label: __("Family") },
	];
	tabs.forEach((t, i) => {
		$tabs.append(`<li class="nav-item"><a class="nav-link ${i ? "" : "active"}" data-tab="${t.id}" href="#">${t.label}</a></li>`);
		$content.append(`<div class="tab-pane ${i ? "" : "active"}" data-pane="${t.id}"></div>`);
	});
	$tabs.on("click", "a", function (e) {
		e.preventDefault();
		const id = $(this).data("tab");
		$tabs.find("a").removeClass("active");
		$(this).addClass("active");
		$content.find("[data-pane]").removeClass("active").filter(`[data-pane='${id}']`).addClass("active");
		render_tab(id);
	});
	const $patientBar = $(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"></div>`).prependTo($body);
	const patient = frappe.ui.form.make_control({
		parent: $patientBar,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), fieldname: "patient" },
		render_input: true,
	});
	patient.$wrapper.css({ minWidth: "260px" });
	patient.refresh();
	patient.$input.on("change", () => {
		state.patient = patient.get_value();
		render_tab("appointments");
	});
	function pane(id) {
		return $content.find(`[data-pane='${id}']`);
	}
	function render_tab(id) {
		const p = state.patient || patient.get_value();
		if (!p && id !== "otp") {
			pane(id).html(`<p class="text-muted">${__("Select a patient record.")}</p>`);
			return;
		}
		if (id === "otp") render_otp();
		if (id === "appointments") load_appointments(p);
		if (id === "labs") load_labs(p);
		if (id === "imaging") load_imaging(p);
		if (id === "pay") render_pay(p);
		if (id === "tele") render_tele(p);
		if (id === "family") load_family(p);
	}
	function render_otp() {
		const $p = pane("otp").empty();
		$p.append(`<div class="form-group"><label>${__("Mobile")}</label><input class="form-control otp-mobile" /></div>`);
		$p.append(`<div class="form-group"><label>${__("OTP")}</label><input class="form-control otp-code" /></div>`);
		$p.append(`<button class="btn btn-default btn-sm btn-send-otp">${__("Send OTP")}</button> `);
		$p.append(`<button class="btn btn-primary btn-sm btn-verify-otp">${__("Verify")}</button>`);
		$p.find(".btn-send-otp").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.patient_otp.send_patient_otp",
				args: { mobile: $p.find(".otp-mobile").val(), patient: state.patient },
				callback(r) {
					if (r.message && r.message.demo_otp) frappe.msgprint(__("Demo OTP: {0}", [r.message.demo_otp]));
					else frappe.show_alert({ message: __("OTP sent"), indicator: "green" });
				},
			});
		});
		$p.find(".btn-verify-otp").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.patient_otp.verify_patient_otp",
				args: { mobile: $p.find(".otp-mobile").val(), otp: $p.find(".otp-code").val(), patient: state.patient },
				callback(r) {
					state.session_token = (r.message || {}).session_token;
					frappe.show_alert({ message: __("Verified"), indicator: "green" });
				},
			});
		});
	}
	function load_appointments(p) {
		frappe.call({
			method: "omnexa_healthcare.api.portal.get_my_appointments",
			args: { patient: p },
			callback(r) {
				const rows = r.message || [];
				pane("appointments").html(rows.length ? `<pre>${JSON.stringify(rows, null, 2)}</pre>` : `<p>${__("No appointments.")}</p>`);
			},
		});
	}
	function load_labs(p) {
		frappe.call({
			method: "omnexa_healthcare.api.portal.get_my_lab_results",
			args: { patient: p },
			callback(r) {
				pane("labs").html(`<pre>${JSON.stringify(r.message || [], null, 2)}</pre>`);
			},
		});
	}
	function load_imaging(p) {
		frappe.call({
			method: "omnexa_healthcare.api.patient_dicom_portal.get_my_imaging_study_urls",
			args: { patient: p },
			callback(r) {
				pane("imaging").html(`<pre>${JSON.stringify(r.message || [], null, 2)}</pre>`);
			},
		});
	}
	function render_pay(p) {
		const $p = pane("pay").empty();
		$p.append(`<div class="form-group"><label>${__("Amount")}</label><input class="form-control pay-amount" type="number" value="100" /></div>`);
		$p.append(`<button class="btn btn-primary btn-sm">${__("Create checkout")}</button><div class="pay-result" style="margin-top:8px"></div>`);
		$p.find("button").on("click", () => {
			const company = frappe.defaults.get_user_default("Company");
			frappe.call({
				method: "omnexa_healthcare.api.patient_payment.create_payment_checkout",
				args: { patient: p, amount: $p.find(".pay-amount").val(), company },
				callback(r) {
					$p.find(".pay-result").html(`<a href="${frappe.utils.escape_html((r.message || {}).checkout_url || "#")}" target="_blank">${__("Open checkout")}</a>`);
				},
			});
		});
	}
	function render_tele(p) {
		pane("tele").html(`<p>${__("Open Telehealth Video Room from workspace after booking a telehealth appointment.")}</p><a class="btn btn-default btn-sm" href="/app/healthcare-telehealth-room">${__("Telehealth room")}</a>`);
	}
	function load_family(p) {
		frappe.call({
			method: "omnexa_healthcare.api.patient_dependents.list_dependents",
			args: { guardian_patient: p },
			callback(r) {
				pane("family").html(`<pre>${JSON.stringify(r.message || [], null, 2)}</pre>`);
			},
		});
	}
	render_tab("otp");
};
