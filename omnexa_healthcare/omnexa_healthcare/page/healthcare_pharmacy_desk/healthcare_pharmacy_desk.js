frappe.pages["healthcare-pharmacy-desk"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Pharmacy Desk"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"></div>`).appendTo($body);
	const $grid = $(`<div class="healthcare-pharmacy-grid"></div>`).appendTo($body);

	const patient = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), fieldname: "patient" },
		render_input: true,
	});
	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), fieldname: "branch", reqd: 1 },
		render_input: true,
	});
	const company = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Company", label: __("Company"), fieldname: "company", reqd: 1 },
		render_input: true,
	});
	const warehouse = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Warehouse", label: __("Warehouse"), fieldname: "warehouse", reqd: 1 },
		render_input: true,
	});
	const item = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Item", label: __("Item"), fieldname: "item", reqd: 1 },
		render_input: true,
	});
	const qty = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Float", label: __("Qty"), fieldname: "qty", default: 1, reqd: 1 },
		render_input: true,
	});
	[patient, branch, company, warehouse, item, qty].forEach((c) => {
		c.$wrapper.css({ minWidth: "180px" });
		c.refresh();
	});

	page.set_primary_action(__("Dispense"), () => dispense());
	page.set_secondary_action(__("Refresh Rx"), () => load_rx());

	function load_rx() {
		frappe.call({
			method: "omnexa_healthcare.api.pharmacy.api_list_active_medications",
			args: { patient: patient.get_value() || "", branch: branch.get_value() || "" },
			callback(r) {
				render_rx(r.message || []);
			},
		});
	}

	function render_rx(rows) {
		$grid.empty();
		if (!rows.length) {
			$grid.html(`<p class="text-muted">${__("No active prescriptions.")}</p>`);
			return;
		}
		const $table = $(
			`<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Patient")}</th><th>${__("Medication")}</th><th>${__("Dosage")}</th><th>${__("Status")}</th>
			</tr></thead><tbody></tbody></table>`
		);
		rows.forEach((row) => {
			const $tr = $(`<tr></tr>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.patient)}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.medication_text || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.dosage_text || "")}</td>`);
			$tr.append(`<td>${frappe.utils.escape_html(row.status || "")}</td>`);
			$tr.on("click", () => {
				patient.set_value(row.patient);
				if (row.branch) branch.set_value(row.branch);
				if (row.company) company.set_value(row.company);
			});
			$table.find("tbody").append($tr);
		});
		$grid.append($table);
	}

	function dispense() {
		const args = {
			patient: patient.get_value(),
			item: item.get_value(),
			qty: qty.get_value(),
			warehouse: warehouse.get_value(),
			branch: branch.get_value(),
			company: company.get_value(),
		};
		if (!args.patient || !args.item || !args.warehouse || !args.branch || !args.company) {
			frappe.msgprint(__("Patient, item, warehouse, branch and company are required."));
			return;
		}
		frappe.call({
			method: "omnexa_healthcare.api.pharmacy.api_pharmacy_pos_dispense",
			args,
			freeze: true,
			callback(r) {
				const msg = r.message || {};
				if (msg.alerts && msg.alerts.length) {
					frappe.msgprint({
						title: __("Drug Interaction Alerts"),
						message: msg.alerts.map((a) => a.description || a.severity).join("<br>"),
						indicator: "orange",
					});
				}
				frappe.show_alert({ message: __("Dispensed {0}", [msg.medication_dispense]), indicator: "green" });
				load_rx();
			},
		});
	}

	load_rx();
};
