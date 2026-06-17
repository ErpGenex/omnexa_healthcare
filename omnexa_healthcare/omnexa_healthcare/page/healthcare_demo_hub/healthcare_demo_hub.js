frappe.pages["healthcare-demo-hub"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Healthcare Demo Hub"),
		single_column: true,
	});

	frappe.call({
		method: "omnexa_healthcare.api.healthcare_role_demo.get_healthcare_demo_credentials",
		callback(r) {
			const data = r.message || {};
			const users = (data.users || [])
				.map(
					(u) =>
						`<tr><td>${frappe.utils.escape_html(u.role)}</td><td><code>${frappe.utils.escape_html(u.email)}</code></td><td><a href="${frappe.utils.escape_html(u.route)}">${frappe.utils.escape_html(u.workspace)}</a></td></tr>`
				)
				.join("");
			$(page.body).html(`
				<div class="panel panel-default">
					<div class="panel-heading"><h4>${__("Healthcare Role Demo")}</h4></div>
					<div class="panel-body">
						<p>${__("Password for all demo users")}: <code>${frappe.utils.escape_html(data.password || "")}</code></p>
						<button class="btn btn-primary btn-seed-demo">${__("Seed Hospital + Role Demo")}</button>
						<hr>
						<table class="table table-bordered table-sm">
							<thead><tr><th>${__("Role")}</th><th>${__("Email")}</th><th>${__("Workspace")}</th></tr></thead>
							<tbody>${users || `<tr><td colspan="3">${__("Run seed first")}</td></tr>`}</tbody>
						</table>
					</div>
				</div>
				<div class="panel panel-default" style="margin-top:16px">
					<div class="panel-heading"><h4>${__("Site Admin — Purge")}</h4></div>
					<div class="panel-body">
						<p class="text-muted">${__("System Manager only. Irreversible.")}</p>
						<button class="btn btn-danger btn-purge-branches">${__("Delete ALL Branches")}</button>
						<button class="btn btn-danger btn-purge-companies">${__("Delete ALL Companies")}</button>
					</div>
				</div>
			`);

			$(page.body).find(".btn-seed-demo").on("click", () => {
				frappe.call({
					method: "omnexa_healthcare.api.healthcare_role_demo.seed_full_healthcare_demo",
					args: { patients: 50 },
					freeze: true,
					callback(res) {
						frappe.msgprint(res.message.message || __("Demo ready"));
						frappe.set_route("healthcare-demo-hub");
					},
				});
			});

			$(page.body).find(".btn-purge-branches").on("click", () => {
				frappe.prompt(
					[{ fieldname: "confirm", label: __('Type "DELETE ALL BRANCHES"'), reqd: 1 }],
					(v) => {
						frappe.call({
							method: "omnexa_core.omnexa_core.site_admin_tools.purge_all_branches",
							args: { confirm_text: v.confirm },
							freeze: true,
							callback(res) {
								frappe.msgprint(__("Deleted {0} branches", [res.message.count]));
							},
						});
					},
					__("Confirm branch purge"),
					__("Delete")
				);
			});

			$(page.body).find(".btn-purge-companies").on("click", () => {
				frappe.prompt(
					[{ fieldname: "confirm", label: __('Type "DELETE ALL COMPANIES"'), reqd: 1 }],
					(v) => {
						frappe.call({
							method: "omnexa_core.omnexa_core.site_admin_tools.purge_all_companies",
							args: { confirm_text: v.confirm },
							freeze: true,
							callback(res) {
								frappe.msgprint(__("Deleted {0} companies", [res.message.count]));
							},
						});
					},
					__("Confirm company purge"),
					__("Delete")
				);
			});
		},
	});
};
