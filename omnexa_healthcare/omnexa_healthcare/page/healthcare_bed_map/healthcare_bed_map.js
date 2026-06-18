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
			method: "omnexa_healthcare.api.specialty_desks.get_bed_board",
			args: { branch: frappe.defaults.get_user_default("Branch") },
			callback(r) {
				$grid.empty();
				const beds = (r.message && r.message.beds) || [];
				if (!beds.length) {
					$grid.html(`<p class="text-muted">${__("No beds found for this branch.")}</p>`);
					return;
				}
				beds.forEach((bed) => {
					const status = bed.occupied ? "Occupied" : bed.status || "Available";
					const c = colors[status] || "#6c757d";
					const label = bed.bed_label || bed.name;
					const $tile = $(`<div style="min-width:120px;padding:10px;border-radius:8px;color:#fff;background:${c};cursor:pointer"></div>`);
					$tile.html(
						`<strong>${frappe.utils.escape_html(label)}</strong><br><small>${frappe.utils.escape_html(status)}</small>` +
							(bed.patient_name ? `<br><small>${frappe.utils.escape_html(bed.patient_name)}</small>` : "")
					);
					$tile.on("click", () => frappe.set_route("Form", "Healthcare Bed", bed.name));
					$grid.append($tile);
				});
			},
		});
	}
	page.set_primary_action(__("Refresh"), () => load());
	load();
};
