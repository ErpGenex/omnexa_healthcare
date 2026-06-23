frappe.pages["healthcare-radiology-worklist"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	const DD = omnexa_healthcare.department;
	if (!OJ || !DD || !DD.mount) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare"));
		return;
	}

	DD.mount(wrapper, {
		deskTitle: __("Radiology Desk"),
		titleAr: "معمل الأشعة",
		titleEn: "Radiology Desk",
		roleAr: "الأشعة",
		roleEn: "Radiology",
		sidebarRole: "radiology",
		homeRoute: "/app/healthcare-workcenter",
		api: "omnexa_healthcare.api.radiology_desk.get_radiology_desk_dashboard",
		defaultTab: "home",
		chartTitle: OJ.t("أنواع الأشعة الأكثر طلباً", "Most Requested Scan Types"),
		chartField: "modality_breakdown",
		chartLabelField: "modality",
		tableTitle: OJ.t("المواعيد القادمة", "Upcoming Appointments"),
		tableField: "upcoming_orders",
		tableColumns: [
			{ field: "authored_on", label: OJ.t("الوقت", "Time") },
			{ field: "patient_display", label: OJ.t("المريض", "Patient") },
			{ field: "request_title", label: OJ.t("نوع الأشعة", "Scan Type") },
			{ field: "status", label: OJ.t("الحالة", "Status") },
		],
		kpiMap(k) {
			return [
				{ value: k.under_reading || 0, label: OJ.t("قيد القراءة", "Under Reading"), hint: OJ.t("قيد المراجعة", "Under review") },
				{ value: k.ready_reports || 0, label: OJ.t("التقارير الجاهزة", "Ready Reports"), hint: OJ.t("جاهز للتسليم", "Ready for delivery") },
				{ value: k.today_scans || 0, label: OJ.t("أشعة اليوم", "Today's Scans") },
				{ value: k.total_scans || 0, label: OJ.t("إجمالي الأشعة", "Total Scans") },
			];
		},
		renderHome($body, data) {
			const reports = data.recent_radiology_reports || [];
			const cards = reports
				.map((r) => {
					const img = r.pacs_wado_url || "";
					const preview = img
						? `<img src="${OJ.esc(img)}" alt="${OJ.esc(r.report_title)}" style="width:100%;height:140px;object-fit:cover;border-radius:8px;background:#111" />`
						: `<div style="height:140px;display:flex;align-items:center;justify-content:center;background:#1a2530;border-radius:8px;color:#7ec8e3">${OJ.t("لا صورة", "No image")}</div>`;
					return `<div class="oj-clinic-card oj-rad-card" data-report="${OJ.esc(r.name)}" style="cursor:pointer;text-align:start">
						${preview}
						<strong style="display:block;margin-top:8px">${OJ.esc(r.report_title)}</strong>
						<span class="oj-muted">${OJ.esc(r.patient_display || r.patient)}</span>
					</div>`;
				})
				.join("");
			$body.html(`
				<div class="oj-kpi-row oj-dept-kpis">${(data.kpis ? [
					{ value: data.kpis.under_reading || 0, label: OJ.t("قيد القراءة", "Under Reading") },
					{ value: data.kpis.ready_reports || 0, label: OJ.t("التقارير الجاهزة", "Ready Reports") },
					{ value: data.kpis.today_scans || 0, label: OJ.t("أشعة اليوم", "Today's Scans") },
					{ value: data.kpis.total_scans || 0, label: OJ.t("إجمالي الأشعة", "Total Scans") },
				] : []).map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${k.value}</div><div class="oj-kpi-label">${k.label}</div></div>`).join("")}</div>
				<div class="oj-panel" style="margin-top:16px">
					<h4>${OJ.t("معرض الأشعة (ديمو)", "Radiology Gallery (Demo)")}</h4>
					<div class="oj-clinic-grid" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr))">${cards || `<p class="oj-muted">${OJ.t("لا تقارير", "No reports")}</p>`}</div>
				</div>
			`);
			$body.find(".oj-rad-card").on("click", function () {
				frappe.set_route("healthcare-dicom-viewer", $(this).attr("data-report"));
			});
		},
		tabs: [
			{ id: "home", ar: "الرئيسية", en: "Home" },
			{ id: "worklist", ar: "قائمة العمل", en: "Worklist" },
			{ id: "stock", ar: "المخزون", en: "Inventory" },
			{ id: "purchases", ar: "المشتريات", en: "Purchases" },
			{ id: "accounts", ar: "الحسابات", en: "Accounts" },
		],
		worklistColumns: [
			{ field: "name", label: OJ.t("الطلب", "Order") },
			{ field: "patient_display", label: OJ.t("المريض", "Patient") },
			{ field: "request_title", label: OJ.t("الدراسة", "Study") },
			{ field: "modality", label: OJ.t("النوع", "Modality") },
			{ field: "priority", label: OJ.t("الأولوية", "Priority") },
			{ field: "status", label: OJ.t("الحالة", "Status") },
		],
		worklistActionLabel: OJ.t("جدولة", "Schedule"),
		onWorklistBind($body, data, reload) {
			$body.find(".oj-wl-action").on("click", async function () {
				const id = $(this).closest("tr").attr("data-row-id");
				try {
					await OJ.call("omnexa_healthcare.api.radiology_desk.schedule_radiology_order", { service_request: id });
					frappe.show_alert({ message: OJ.t("تمت الجدولة", "Scheduled"), indicator: "green" });
					reload();
				} catch (e) {
					OJ.showCallError(e);
				}
			});
		},
		homeFooterHtml() {
			return `<div class="oj-nav-actions">
				<button type="button" class="oj-btn oj-btn-outline" data-route="/app/healthcare-dicom-viewer">${OJ.t("عارض DICOM", "DICOM Viewer")}</button>
				<button type="button" class="oj-btn oj-btn-primary" data-route="List/Healthcare Service Request">${OJ.t("عرض جميع المواعيد", "View all appointments")}</button>
			</div>`;
		},
	});
};
