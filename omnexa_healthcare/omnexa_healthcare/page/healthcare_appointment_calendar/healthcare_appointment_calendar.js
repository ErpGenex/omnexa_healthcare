frappe.pages["healthcare-appointment-calendar"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Appointment Calendar"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"></div>`).appendTo($body);
	const $grid = $(`<div class="healthcare-calendar-grid"></div>`).appendTo($body);

	const practitioner = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Practitioner", label: __("Practitioner"), fieldname: "practitioner", reqd: 1 },
		render_input: true,
	});
	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), fieldname: "branch", reqd: 1 },
		render_input: true,
	});
	const specialty = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Specialty", label: __("Specialty"), fieldname: "specialty" },
		render_input: true,
	});
	const date = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Date", label: __("Date"), fieldname: "date", default: frappe.datetime.get_today(), reqd: 1 },
		render_input: true,
	});
	[practitioner, branch, specialty, date].forEach((c) => {
		c.$wrapper.css({ minWidth: "200px" });
		c.refresh();
	});

	page.set_primary_action(__("Load slots"), () => load_slots());

	function load_slots() {
		const args = {
			practitioner: practitioner.get_value(),
			branch: branch.get_value(),
			date: date.get_value(),
			specialty: specialty.get_value() || "",
		};
		if (!args.practitioner || !args.branch || !args.date) {
			frappe.msgprint(__("Practitioner, branch and date are required."));
			return;
		}
		frappe.call({
			method: "omnexa_healthcare.api.scheduling.api_get_available_slots",
			args,
			freeze: true,
			callback(r) {
				render_slots(r.message || []);
			},
		});
	}

	function render_slots(slots) {
		$grid.empty();
		if (!slots.length) {
			$grid.html(`<p class="text-muted">${__("No open slots. Check practitioner schedule and branch assignment.")}</p>`);
			return;
		}
		const $table = $(`<table class="table table-bordered table-sm"><thead><tr><th>${__("Start")}</th><th>${__("End")}</th><th>${__("Fee")}</th></tr></thead><tbody></tbody></table>`);
		slots.forEach((s) => {
			$table.find("tbody").append(
				`<tr><td>${frappe.utils.escape_html(s.start)}</td><td>${frappe.utils.escape_html(s.end)}</td><td>${s.consultation_fee || 0}</td></tr>`
			);
		});
		$grid.append($table);
	}
};
