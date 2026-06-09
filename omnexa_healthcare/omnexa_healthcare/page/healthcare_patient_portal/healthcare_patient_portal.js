frappe.pages["healthcare-patient-portal"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Patient Portal"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"></div>`).appendTo($body);
	const $appointments = $(`<div class="portal-appointments"></div>`).appendTo($body);
	const $register = $(`<div class="portal-register" style="margin-top:24px"></div>`).appendTo($body);

	const patient = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("My Patient Record"), fieldname: "patient" },
		render_input: true,
	});
	patient.$wrapper.css({ minWidth: "280px" });
	patient.refresh();

	page.set_primary_action(__("My Appointments"), () => load_appointments());

	function load_appointments() {
		const p = patient.get_value();
		if (!p) {
			frappe.msgprint(__("Select your patient record."));
			return;
		}
		frappe.call({
			method: "omnexa_healthcare.api.portal.get_my_appointments",
			args: { patient: p },
			freeze: true,
			callback(r) {
				render_appointments(r.message || []);
			},
		});
	}

	function render_appointments(rows) {
		$appointments.empty();
		if (!rows.length) {
			$appointments.html(`<p class="text-muted">${__("No appointments on file.")}</p>`);
			return;
		}
		const $table = $(
			`<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Date")}</th><th>${__("Practitioner")}</th><th>${__("Specialty")}</th><th>${__("Status")}</th>
			</tr></thead><tbody></tbody></table>`
		);
		rows.forEach((row) => {
			const $tr = $(`<tr></tr>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.appointment_date || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.practitioner || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.specialty || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.status || "")}</td>`);
			$table.find("tbody").append($tr);
		});
		$appointments.append(`<h5>${__("Appointments")}</h5>`).append($table);
	}

	$register.html(`<h5>${__("Self Registration")}</h5>`);
	const fields = ["given_name", "family_name", "email", "company", "branch"];
	const controls = {};
	fields.forEach((f) => {
		const df = {
			fieldname: f,
			label: __(f.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())),
			fieldtype: f === "email" ? "Data" : "Link",
			options: f === "company" ? "Company" : f === "branch" ? "Branch" : undefined,
			reqd: 1,
		};
		controls[f] = frappe.ui.form.make_control({ parent: $register, df, render_input: true });
		controls[f].$wrapper.css({ maxWidth: "320px", marginBottom: "8px" });
		controls[f].refresh();
	});
	$(`<button class="btn btn-primary">${__("Register")}</button>`)
		.appendTo($register)
		.on("click", () => {
			const payload = {};
			fields.forEach((f) => (payload[f] = controls[f].get_value()));
			frappe.call({
				method: "omnexa_healthcare.api.portal.register_portal_patient",
				args: { payload },
				freeze: true,
				callback(r) {
					const msg = r.message || {};
					frappe.msgprint(__("Registered patient {0}", [msg.patient]));
					if (msg.patient) patient.set_value(msg.patient);
				},
			});
		});
};
