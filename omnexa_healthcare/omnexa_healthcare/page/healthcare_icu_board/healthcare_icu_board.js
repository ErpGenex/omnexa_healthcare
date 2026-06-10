frappe.pages["healthcare-icu-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("ICU / NICU Monitoring Board"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div class="d-flex flex-wrap gap-2 mb-3 align-items-end"></div>`).appendTo($body);
	const $grid = $(`<div></div>`).appendTo($body);

	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), reqd: 1 },
		render_input: true,
	});
	branch.$wrapper.css({ minWidth: "220px" });

	const unitFilter = frappe.ui.form.make_control({
		parent: $toolbar,
		df: {
			fieldtype: "Select",
			label: __("Care unit"),
			options: "\nICU\nNICU\nNursery",
		},
		render_input: true,
	});
	unitFilter.$wrapper.css({ minWidth: "160px" });
	unitFilter.refresh();

	page.set_primary_action(__("Refresh"), () => load());
	setInterval(() => load(true), 60000);

	function alertClass(level) {
		if (level === "Critical") return "red";
		if (level === "Warning") return "orange";
		return "green";
	}

	function load(silent) {
		if (!branch.get_value()) return;
		frappe.call({
			method: "omnexa_healthcare.api.critical_care.api_get_critical_care_board",
			args: { branch: branch.get_value(), care_unit: unitFilter.get_value() || null },
			freeze: !silent,
			callback(r) {
				const rows = r.message || [];
				$grid.empty();
				if (!rows.length) {
					$grid.html(`<p class="text-muted">${__("No patients in ICU / NICU / Nursery beds.")}</p>`);
					return;
				}
				const $t = $(
					`<table class="table table-bordered table-sm"><thead class="table-light"><tr>
					<th>${__("Bed")}</th><th>${__("Patient")}</th><th>${__("Unit")}</th>
					<th>HR</th><th>RR</th><th>SpO2</th><th>BP</th><th>Temp</th>
					<th>${__("FiO2")}</th><th>${__("Weight (g)")}</th><th>${__("Alert")}</th>
					<th>${__("Last vitals")}</th><th>${__("Actions")}</th>
					</tr></thead><tbody></tbody></table>`
				);
				rows.forEach((row) => {
					const bp = [row.bp_systolic, row.bp_diastolic].filter(Boolean).join("/") || "—";
					const alert = row.alert_level || "Normal";
					const mins = row.minutes_since_vitals;
					const stale = mins != null && mins > 60;
					const $tr = $(`<tr></tr>`);
					if (alert === "Critical") $tr.addClass("table-danger");
					else if (alert === "Warning") $tr.addClass("table-warning");
					$tr.append(`<td><b>${frappe.utils.escape_html(row.bed_label || row.bed)}</b><br>
						<span class="small text-muted">${frappe.utils.escape_html(row.bed_type || "")}</span></td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.patient_display || row.patient)}</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.unit_name || row.care_unit || "")}</td>`);
					$tr.append(`<td>${row.heart_rate ?? "—"}</td><td>${row.respiratory_rate ?? "—"}</td>`);
					$tr.append(`<td>${row.spo2 ?? "—"}</td><td>${bp}</td><td>${row.temperature_c ?? "—"}</td>`);
					$tr.append(`<td>${row.fio2_percent ?? "—"}</td><td>${row.weight_g ?? "—"}</td>`);
					$tr.append(
						`<td><span class="indicator-pill ${alertClass(alert)} filterable no-indicator-dot">${__(
							alert
						)}</span></td>`
					);
					$tr.append(
						`<td class="small ${stale ? "text-danger" : "text-muted"}">${
							row.last_recorded_at
								? frappe.datetime.str_to_user(row.last_recorded_at) +
								  (mins != null ? ` (${mins}m)` : "")
								: __("No vitals")
						}</td>`
					);
					const $a = $(`<td class="text-nowrap"></td>`);
					$a.append(
						$(`<button class="btn btn-xs btn-primary" style="margin:2px">${__("Record vitals")}</button>`).on(
							"click",
							() => promptVitals(row)
						)
					);
					$a.append(
						$(`<button class="btn btn-xs btn-default" style="margin:2px">${__("Open admission")}</button>`).on(
							"click",
							() => frappe.set_route("Form", "Healthcare Admission", row.admission)
						)
					);
					$tr.append($a);
					$t.find("tbody").append($tr);
				});
				$grid.append($t);
			},
		});
	}

	function promptVitals(row) {
		const isNeonatal = ["NICU", "Nursery"].includes(row.care_unit) || ["NICU", "Nursery"].includes(row.bed_type);
		const fields = [
			{ fieldname: "heart_rate", fieldtype: "Int", label: __("Heart Rate (bpm)") },
			{ fieldname: "respiratory_rate", fieldtype: "Int", label: __("Respiratory Rate") },
			{ fieldname: "spo2", fieldtype: "Float", label: __("SpO2 (%)") },
			{ fieldname: "bp_systolic", fieldtype: "Int", label: __("BP Systolic") },
			{ fieldname: "bp_diastolic", fieldtype: "Int", label: __("BP Diastolic") },
			{ fieldname: "temperature_c", fieldtype: "Float", label: __("Temperature (°C)") },
			{ fieldname: "fio2_percent", fieldtype: "Float", label: __("FiO2 (%)") },
			{ fieldname: "ventilator_mode", fieldtype: "Data", label: __("Ventilator Mode") },
		];
		if (isNeonatal) {
			fields.push(
				{ fieldname: "weight_g", fieldtype: "Float", label: __("Weight (g)") },
				{ fieldname: "gestational_age_weeks", fieldtype: "Float", label: __("Gestational Age (weeks)") }
			);
		}
		fields.push({ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") });

		frappe.prompt(
			fields,
			(values) => {
				frappe.call({
					method: "omnexa_healthcare.api.critical_care.record_monitoring",
					args: {
						payload: {
							patient: row.patient,
							admission: row.admission,
							bed: row.bed,
							care_unit: row.care_unit,
							company: frappe.defaults.get_default("company"),
							branch: branch.get_value(),
							...values,
						},
					},
					callback() {
						frappe.show_alert({ message: __("Vitals recorded"), indicator: "green" });
						load(true);
					},
				});
			},
			__("Record ICU / NICU vitals"),
			__("Save")
		);
	}

	branch.$input.on("change", () => load());
	unitFilter.$input.on("change", () => load());
	load();
};
