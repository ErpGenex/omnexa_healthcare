frappe.pages["healthcare-patient-queue"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Patient Queue"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"></div>`).appendTo($body);
	const $grid = $(`<div class="healthcare-queue-grid"></div>`).appendTo($body);

	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), fieldname: "branch", reqd: 1 },
		render_input: true,
	});
	const service_unit = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Service Unit", label: __("Service Unit"), fieldname: "service_unit" },
		render_input: true,
	});
	const queue_date = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Date", label: __("Date"), fieldname: "queue_date", default: frappe.datetime.get_today(), reqd: 1 },
		render_input: true,
	});
	[branch, service_unit, queue_date].forEach((c) => {
		c.$wrapper.css({ minWidth: "200px" });
		c.refresh();
	});

	page.set_primary_action(__("Refresh"), () => load_queue());
	setInterval(() => load_queue(true), 60000);

	function load_queue(silent) {
		const args = {
			branch: branch.get_value(),
			service_unit: service_unit.get_value() || "",
			queue_date: queue_date.get_value(),
		};
		if (!args.branch) {
			if (!silent) frappe.msgprint(__("Branch is required."));
			return;
		}
		frappe.call({
			method: "omnexa_healthcare.api.queue.api_get_patient_queue",
			args,
			freeze: !silent,
			callback(r) {
				render_queue(r.message || []);
			},
		});
	}

	function render_queue(rows) {
		$grid.empty();
		if (!rows.length) {
			$grid.html(`<p class="text-muted">${__("No patients in queue for this branch/date.")}</p>`);
			return;
		}
		const $table = $(
			`<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Patient")}</th><th>${__("Practitioner")}</th><th>${__("Time")}</th>
				<th>${__("Triage")}</th><th>${__("Status")}</th><th>${__("Wait (min)")}</th><th>${__("Actions")}</th>
			</tr></thead><tbody></tbody></table>`
		);
		rows.forEach((row) => {
			const $tr = $(`<tr></tr>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.patient_display || row.patient)}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.practitioner || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.appointment_date || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.triage_level || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.status || "")}</td>`);
			$tr.append(`<td>${row.wait_mins || 0}</td>`);
			const $actions = $(`<td></td>`);
			["Arrived", "In Consultation", "Completed", "No Show"].forEach((st) => {
				$actions.append(
					$(`<button class="btn btn-xs btn-default" style="margin-right:4px">${__(st)}</button>`).on("click", () =>
						update_status(row.name, st)
					)
				);
			});
			$tr.append($actions);
			$table.find("tbody").append($tr);
		});
		$grid.append($table);
	}

	function update_status(name, status) {
		frappe.call({
			method: "omnexa_healthcare.api.queue.api_update_queue_status",
			args: { appointment: name, status },
			freeze: true,
			callback() {
				frappe.show_alert({ message: __("Queue updated"), indicator: "green" });
				load_queue(true);
			},
		});
	}
};
