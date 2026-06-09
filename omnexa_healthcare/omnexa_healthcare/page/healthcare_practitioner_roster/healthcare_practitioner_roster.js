frappe.pages["healthcare-practitioner-roster"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Practitioner Roster"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"></div>`).appendTo($body);
	const $grid = $(`<div></div>`).appendTo($body);

	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), fieldname: "branch" },
		render_input: true,
	});
	const roster_date = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Date", label: __("Date"), fieldname: "roster_date", default: frappe.datetime.get_today() },
		render_input: true,
	});
	[branch, roster_date].forEach((c) => {
		c.$wrapper.css({ minWidth: "200px" });
		c.refresh();
	});

	page.set_primary_action(__("Refresh"), () => load_roster());

	function load_roster() {
		frappe.call({
			method: "omnexa_healthcare.api.scheduling.api_get_practitioner_roster",
			args: { branch: branch.get_value() || "", roster_date: roster_date.get_value() },
			freeze: true,
			callback(r) {
				render_roster(r.message || []);
			},
		});
	}

	function render_roster(rows) {
		$grid.empty();
		if (!rows.length) {
			$grid.html(`<p class="text-muted">${__("No active practitioners found.")}</p>`);
			return;
		}
		const $table = $(
			`<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Practitioner")}</th><th>${__("License")}</th><th>${__("Branches / Specialty")}</th>
				<th>${__("Appointments")}</th><th>${__("Actions")}</th>
			</tr></thead><tbody></tbody></table>`
		);
		rows.forEach((row) => {
			const branch_text = (row.branches || [])
				.map((b) => `${b.branch}${b.specialty ? " · " + b.specialty : ""}`)
				.join("<br>");
			const $tr = $(`<tr></tr>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.practitioner_name)}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.license_number || "")}</td>`);
			$tr.append(`<td>${branch_text}</td>`);
			$tr.append(`<td>${row.appointment_count || 0}</td>`);
			const $actions = $(`<td></td>`);
			$actions.append(
				$(`<button class="btn btn-xs btn-default">${__("Open")}</button>`).on("click", () =>
					frappe.set_route("Form", "Healthcare Practitioner", row.name)
				)
			);
			$tr.append($actions);
			$table.find("tbody").append($tr);
		});
		$grid.append($table);
	}

	load_roster();
};
