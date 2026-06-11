frappe.pages["healthcare-bed-map"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Visual Bed Map"),
		single_column: true,
	});
	const $body = $(page.body);
	const $grid = $(`<div class="bed-map-grid" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px"></div>`).appendTo($body);
	const colors = { Available: "#198754", Occupied: "#dc3545", Maintenance: "#ffc107", Reserved: "#0d6efd" };
	function load() {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Healthcare Bed",
				fields: ["name", "bed_name", "status", "bed_type", "ward"],
				limit_page_length: 500,
			},
			callback(r) {
				$grid.empty();
				(r.message || []).forEach((bed) => {
					const c = colors[bed.status] || "#6c757d";
					const $tile = $(`<div style="min-width:120px;padding:10px;border-radius:8px;color:#fff;background:${c};cursor:pointer"></div>`);
					$tile.html(`<strong>${frappe.utils.escape_html(bed.bed_name || bed.name)}</strong><br><small>${frappe.utils.escape_html(bed.status || "")}</small>`);
					$tile.on("click", () => frappe.set_route("Form", "Healthcare Bed", bed.name));
					$grid.append($tile);
				});
			},
		});
	}
	page.set_primary_action(__("Refresh"), () => load());
	load();
};
