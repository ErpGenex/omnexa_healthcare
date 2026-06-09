frappe.pages["healthcare-er-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("ER Board"), single_column: true });
	const $body = $(page.body);
	const $toolbar = $(`<div style="margin-bottom:12px;display:flex;gap:8px"></div>`).appendTo($body);
	const $grid = $(`<div></div>`).appendTo($body);
	const branch = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Branch", label: __("Branch"), reqd: 1 },
		render_input: true,
	});
	branch.$wrapper.css({ minWidth: "220px" });
	branch.refresh();
	page.set_primary_action(__("Refresh"), () => load());
	setInterval(() => load(true), 30000);
	function load(silent) {
		if (!branch.get_value()) return;
		frappe.call({
			method: "omnexa_healthcare.api.er.api_get_er_board",
			args: { branch: branch.get_value() },
			freeze: !silent,
			callback(r) {
				const rows = r.message || [];
				$grid.empty();
				if (!rows.length) {
					$grid.html(`<p class="text-muted">${__("No active ER visits.")}</p>`);
					return;
				}
				const $t = $(
					`<table class="table table-bordered table-sm"><thead><tr>
					<th>ESI</th><th>${__("Patient")}</th><th>${__("Arrival")}</th><th>${__("Wait")}</th>
					<th>${__("Track")}</th><th>${__("Status")}</th><th>${__("Actions")}</th>
					</tr></thead><tbody></tbody></table>`
				);
				rows.forEach((row) => {
					const $tr = $(`<tr></tr>`);
					$tr.append(`<td><b>${row.esi_level}</b></td><td>${frappe.utils.escape_html(row.patient)}</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.arrival_datetime || "")}</td><td>${row.wait_mins || 0}m</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.track || "")}</td><td>${frappe.utils.escape_html(row.status)}</td>`);
					const $a = $(`<td></td>`);
					["Triaged", "In Treatment", "Disposition"].forEach((st) => {
						$a.append(
							$(`<button class="btn btn-xs btn-default" style="margin:2px">${__(st)}</button>`).on("click", () =>
								frappe.call({
									method: "omnexa_healthcare.api.er.update_er_status",
									args: { name: row.name, status: st },
									callback: () => load(true),
								})
							)
						);
					});
					$tr.append($a);
					$t.find("tbody").append($tr);
				});
				$grid.append($t);
			},
		});
	}
	load();
};
