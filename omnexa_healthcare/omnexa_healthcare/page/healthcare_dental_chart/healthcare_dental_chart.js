frappe.pages["healthcare-dental-chart"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Interactive Dental Chart"), single_column: true });
	const $root = $(`<div></div>`).appendTo(page.body);
	const $controls = $(`<div class="row mb-3"></div>`).appendTo($root);
	const patient = frappe.ui.form.make_control({
		parent: $controls,
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient"), reqd: 1 },
		render_input: true,
	});
	patient.$wrapper.addClass("col-md-4");
	const numbering = frappe.ui.form.make_control({
		parent: $controls,
		df: { fieldtype: "Select", label: __("Tooth Numbering System"), options: "FDI\nUniversal", default: "FDI" },
		render_input: true,
	});
	numbering.$wrapper.addClass("col-md-3");
	const $grid = $(`<div id="hc-dental-grid" class="d-flex flex-wrap gap-2 mb-3"></div>`).appendTo($root);
	const $detail = $(`<div class="card"><div class="card-body" id="hc-dental-detail"></div></div>`).appendTo($root);

	function loadChart() {
		const p = patient.get_value();
		if (!p) return;
		frappe.call({
			method: "omnexa_healthcare.api.dental.get_patient_dental_chart",
			args: { patient: p, numbering_system: numbering.get_value() || "FDI" },
			callback(r) {
				const data = r.message || {};
				const entries = {};
				(data.entries || []).forEach((e) => {
					entries[e.tooth_id] = e;
				});
				$grid.empty();
				(data.tooth_map?.teeth || []).forEach((tooth) => {
					const e = entries[String(tooth)];
					const cond = e?.condition || "healthy";
					const cls = cond === "healthy" ? "btn-outline-secondary" : "btn-primary";
					$(`<button class="btn btn-sm ${cls}" data-tooth="${tooth}">${tooth}</button>`)
						.appendTo($grid)
						.on("click", () => editTooth(p, tooth, e));
				});
			},
		});
	}

	function editTooth(p, tooth, existing) {
		const d = new frappe.ui.Dialog({
			title: __("Tooth {0}", [tooth]),
			fields: [
				{ fieldtype: "Select", fieldname: "condition", label: __("Condition"), options: "healthy\ncaries\nfilled\ncrown\nimplant\nmissing\nroot_canal", default: existing?.condition || "healthy" },
				{ fieldtype: "Select", fieldname: "surface", label: __("Surface"), options: "\nM\nD\nO\nB\nL" },
				{ fieldtype: "Small Text", fieldname: "treatment_plan", label: __("Treatment Plan"), default: existing?.treatment_plan },
			],
			primary_action_label: __("Save"),
			primary_action(values) {
				frappe.call({
					method: "omnexa_healthcare.api.dental.upsert_dental_chart_entry",
					args: {
						patient: p,
						tooth_id: String(tooth),
						company: frappe.defaults.get_user_default("Company"),
						branch: frappe.defaults.get_user_default("Branch"),
						numbering_system: numbering.get_value(),
						...values,
					},
					callback() {
						d.hide();
						loadChart();
					},
				});
			},
		});
		d.show();
	}

	page.set_primary_action(__("Load Chart"), loadChart);
	patient.refresh();
	numbering.refresh();
};
