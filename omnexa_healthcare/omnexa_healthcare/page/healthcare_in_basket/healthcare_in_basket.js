frappe.pages["healthcare-in-basket"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("In Basket"), single_column: true });
	const $grid = $(`<div></div>`).appendTo(page.body);
	page.set_primary_action(__("Refresh"), () => load());
	function load() {
		frappe.call({
			method: "omnexa_healthcare.api.in_basket.api_get_in_basket",
			args: { status: "Open" },
			callback(r) {
				const rows = r.message || [];
				$grid.empty();
				if (!rows.length) {
					$grid.html(`<p class="text-muted">${__("In Basket is empty.")}</p>`);
					return;
				}
				const $t = $(
					`<table class="table table-bordered table-sm"><thead><tr>
					<th>${__("Priority")}</th><th>${__("Type")}</th><th>${__("Subject")}</th><th>${__("Patient")}</th><th></th>
					</tr></thead><tbody></tbody></table>`
				);
				rows.forEach((row) => {
					const $tr = $(`<tr></tr>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.priority)}</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.item_type)}</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.subject)}</td>`);
					$tr.append(`<td>${frappe.utils.escape_html(row.patient || "")}</td>`);
					const $a = $(`<td></td>`);
					$a.append(
						$(`<button class="btn btn-xs btn-primary">${__("Done")}</button>`).on("click", () =>
							frappe.call({
								method: "omnexa_healthcare.api.in_basket.complete_in_basket_item",
								args: { name: row.name },
								callback: () => load(),
							})
						)
					);
					$tr.append($a);
					$t.find("tbody").append($tr);
				});
				$grid.append($t);
			},
		});
	}
	load();
};
