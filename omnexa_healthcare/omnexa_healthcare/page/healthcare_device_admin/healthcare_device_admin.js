frappe.pages["healthcare-device-admin"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, __("Medical Device Integration"));

	async function render() {
		const data = await OJ.call("omnexa_healthcare.api.device_integration.get_device_admin_dashboard", { company, branch });
		const $body = $("<div></div>");
		$body.append(`<div class="oj-filter-bar">
			<button type="button" class="oj-btn oj-btn-primary oj-add-device">${OJ.t("تسجيل جهاز", "Register Device")}</button>
			<button type="button" class="oj-btn oj-btn-outline oj-seed-dev">${OJ.t("أجهزة تجريبية", "Seed Demo Devices")}</button>
		</div>`);
		$body.append(`<h4>${OJ.t("الأجهزة النشطة", "Active Devices")} (${data.active_count || 0})</h4>`);
		$body.append(
			OJ.dataTable(
				[
					{ field: "device_code", label: OJ.t("الكود", "Code") },
					{ field: "device_name", label: OJ.t("الاسم", "Name") },
					{ field: "device_type", label: OJ.t("النوع", "Type") },
					{ field: "integration_protocol", label: OJ.t("البروتوكول", "Protocol") },
					{ field: "manufacturer", label: OJ.t("الشركة", "Manufacturer") },
				],
				data.devices || []
			)
		);
		$body.append(`<h4 style="margin-top:16px">${OJ.t("ربط الأقسام والتخصصات", "Department Integration Map")}</h4>`);
		const deptRows = (data.department_map || []).map((d) => ({
			department: OJ.lang() === "ar" ? d.department_ar : d.department_en,
			device_types: (d.device_types || []).join(", "),
			protocols: (d.protocols || data.protocols || []).slice(0, 3).join(", "),
		}));
		$body.append(
			OJ.dataTable(
				[
					{ field: "department", label: OJ.t("القسم", "Department") },
					{ field: "device_types", label: OJ.t("أنواع الأجهزة", "Device Types") },
					{ field: "protocols", label: OJ.t("البروتوكولات", "Protocols") },
				],
				deptRows
			)
		);
		$body.find(".oj-add-device").on("click", () => {
			frappe.prompt(
				[
					{ fieldname: "device_code", label: __("Device Code"), reqd: 1 },
					{ fieldname: "device_name", label: __("Device Name"), reqd: 1 },
					{
						fieldname: "device_type",
						label: __("Device Type"),
						fieldtype: "Select",
						options: (data.device_types || []).join("\n"),
						default: "Vital Signs Monitor",
					},
					{
						fieldname: "integration_protocol",
						label: __("Protocol"),
						fieldtype: "Select",
						options: (data.protocols || []).join("\n"),
						default: "HL7_ORU",
					},
					{ fieldname: "manufacturer", label: __("Manufacturer") },
				],
				(v) => {
					frappe.call({
						method: "omnexa_healthcare.api.device_integration.register_medical_device",
						args: { ...v, company, branch },
						callback() {
							frappe.show_alert({ message: __("Device registered"), indicator: "green" });
							render();
						},
					});
				},
				__("Register Medical Device")
			);
		});
		$body.find(".oj-seed-dev").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.device_integration.seed_demo_medical_devices",
				args: { company, branch },
				callback() {
					render();
				},
			});
		});
		const $shell = OJ.shell({
			title: OJ.t("ربط الأجهزة الطبية", "Medical Device Integration"),
			subtitle: OJ.t("HL7 · ASTM · DICOM · FHIR · MQTT · REST", "HL7 · ASTM · DICOM · FHIR · MQTT · REST"),
			role: OJ.t("مدير النظام", "System Admin"),
			kpis: [
				{ value: data.active_count || 0, label: OJ.t("أجهزة نشطة", "Active") },
				{ value: (data.protocols || []).length, label: OJ.t("بروتوكولات", "Protocols") },
				{ value: (data.device_types || []).length, label: OJ.t("أنواع", "Types") },
			],
			sidebar: OJ.defaultSidebar("admin"),
			bodyEl: $body,
			homeRoute: "/app/healthcare-demo-hub",
		});
		$mount.empty().append($shell);
	}

	render().catch((e) => OJ.showCallError(e));
};
