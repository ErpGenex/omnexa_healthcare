frappe.pages["healthcare-demo-hub"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) {
		frappe.ui.make_app_page({ parent: wrapper, title: __("Healthcare Demo Hub"), single_column: true });
		return;
	}
	const $mount = OJ.mountDeskPage(wrapper, __("Healthcare Demo Hub"));

	async function render() {
		const [creds, groups] = await Promise.all([
			OJ.call("omnexa_healthcare.api.healthcare_role_demo.get_healthcare_demo_credentials"),
			OJ.call("omnexa_healthcare.api.portal_catalog.get_grouped_portal_catalog"),
		]);
		const $body = $("<div class='oj-demo-hub'></div>");
		$body.append(`<div class="oj-panel"><h4>${OJ.t("حسابات الديمو", "Demo Accounts")}</h4>
			<p class="oj-muted">${OJ.t("كلمة المرور", "Password")}: <code>${OJ.esc(creds.password)}</code></p>
			<div class="oj-filter-bar">
				<button type="button" class="oj-btn oj-btn-primary oj-seed-demo">${OJ.t("زرع المستشفى + الديمو", "Seed Hospital + Demo")}</button>
				<button type="button" class="oj-btn oj-btn-outline oj-sync-perms">${OJ.t("مزامنة الصلاحيات", "Sync Permissions")}</button>
				<button type="button" class="oj-btn oj-btn-outline oj-seed-devices">${OJ.t("أجهزة تجريبية", "Seed Demo Devices")}</button>
			</div>
			${OJ.dataTable(
				[
					{ field: "role", label: OJ.t("الدور", "Role") },
					{ field: "email", label: OJ.t("البريد", "Email") },
					{ field: "name", label: OJ.t("الاسم", "Name") },
					{ field: "route", label: OJ.t("البوابة", "Portal") },
				],
				(creds.users || []).map((u) => ({ ...u, route: u.route }))
			)}
		</div>`);
		$body.append(`<div class="oj-panel oj-demo-portals-panel" style="margin-top:16px"><h4>${OJ.t("جميع البوابات", "All Portals")}</h4></div>`);
		const $portalMount = $body.find(".oj-demo-portals-panel");
		(groups || []).forEach((g) => {
			const title = OJ.lang() === "ar" ? g.label_ar : g.label_en;
			$portalMount.append(`<h4 class="oj-portal-cat-title" style="margin-top:20px">${OJ.esc(title)}</h4>`);
			const clinics = (g.portals || []).map((p) => ({
				id: p.id,
				name: OJ.lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: OJ.t("بوابة خارجية", "Outpatient portal"),
				icon: p.icon || "🏥",
				doctor_count: 1,
				waiting_count: 0,
				route: p.route,
				exists: p.exists,
			}));
			$portalMount.append(
				OJ.clinicGrid(
					clinics.filter((c) => c.exists !== false && c.route),
					(c) => OJ.navigateRoute(c.route)
				)
			);
		});
		$body.find(".oj-seed-demo").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.healthcare_role_demo.seed_full_healthcare_demo",
				args: { patients: 50 },
				freeze: true,
				callback(r) {
					frappe.msgprint(r.message.message || __("Demo ready"));
					render();
				},
			});
		});
		$body.find(".oj-sync-perms").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.utils.healthcare_demo_permissions.sync_healthcare_demo_permissions",
				freeze: true,
				callback() {
					frappe.show_alert({ message: __("Permissions synced"), indicator: "green" });
				},
			});
		});
		$body.find(".oj-seed-devices").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.device_integration.seed_demo_medical_devices",
				freeze: true,
				callback() {
					frappe.show_alert({ message: __("Devices seeded"), indicator: "green" });
				},
			});
		});
		const $shell = OJ.shell({
			title: OJ.t("مركز تجربة Omnexa Healthcare", "Omnexa Healthcare Demo Hub"),
			subtitle: OJ.t("كل البوابات · كل الأدوار · كل الأقسام", "All portals · roles · departments"),
			role: OJ.t("مدير النظام", "System Manager"),
			sidebar: OJ.defaultSidebar("admin"),
			bodyEl: $body,
			homeRoute: "/app/healthcare-demo-hub",
		});
		$mount.empty().append($shell);
	}

	render().catch((e) => OJ.showCallError(e));
};
