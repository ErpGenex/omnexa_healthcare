frappe.pages["healthcare-lab-workbench"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	const DD = omnexa_healthcare.department;
	if (!OJ || !DD || !DD.mount) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare"));
		return;
	}

	const PRINT_FMT = "Omnexa Lab Report";

	function printLabReport(reportName) {
		if (!reportName) return;
		const params = new URLSearchParams({
			doctype: "Healthcare Diagnostic Report",
			name: reportName,
			format: PRINT_FMT,
			no_letterhead: "1",
		});
		window.open(frappe.urllib.get_full_url(`/printview?${params.toString()}`), "_blank");
	}

	DD.mount(wrapper, {
		deskTitle: __("Laboratory Desk"),
		titleAr: "معمل التحاليل",
		titleEn: "Laboratory Desk",
		roleAr: "معمل التحاليل",
		roleEn: "Laboratory",
		sidebarRole: "lab",
		homeRoute: "/app/healthcare-demo-hub",
		api: "omnexa_healthcare.api.lab_desk.get_lab_desk_dashboard",
		defaultTab: "home",
		chartTitle: OJ.t("التحاليل الأكثر طلباً", "Most Requested Tests"),
		chartField: "top_tests",
		chartLabelField: "test_name",
		showDevices: true,
		kpiMap(k) {
			return [
				{ value: k.in_progress || 0, label: OJ.t("قيد التنفيذ", "In Progress"), hint: OJ.t("عمل جاري", "Work in progress") },
				{ value: k.ready_results || 0, label: OJ.t("النتائج الجاهزة", "Ready Results"), hint: OJ.t("جاهز للتسليم", "Ready for delivery") },
				{ value: k.today_tests || 0, label: OJ.t("تحاليل اليوم", "Today's Tests") },
				{ value: k.total_tests || 0, label: OJ.t("إجمالي التحاليل", "Total Tests") },
			];
		},
		renderHome($body, data) {
			const kpis = [
				{ value: (data.kpis || {}).in_progress || 0, label: OJ.t("قيد التنفيذ", "In Progress") },
				{ value: (data.kpis || {}).ready_results || 0, label: OJ.t("النتائج الجاهزة", "Ready Results") },
				{ value: (data.kpis || {}).today_tests || 0, label: OJ.t("تحاليل اليوم", "Today's Tests") },
				{ value: (data.kpis || {}).total_tests || 0, label: OJ.t("إجمالي التحاليل", "Total Tests") },
			];
			const deviceRows = (data.devices || []).map((d) => ({
				...d,
				modality: d.modality || d.protocol || "—",
			}));
			const reports = data.recent_lab_reports || [];
			const reportRows = reports
				.map(
					(r) => `<tr data-report="${OJ.esc(r.name)}">
						<td>${OJ.esc(r.name)}</td>
						<td>${OJ.esc(r.patient_display)}</td>
						<td>${OJ.esc(r.report_title)}</td>
						<td>${OJ.esc(r.status)}</td>
						<td><button type="button" class="oj-btn oj-btn-sm oj-btn-primary oj-print-lab">${OJ.t("طباعة", "Print")}</button></td>
					</tr>`
				)
				.join("");
			$body.html(`
				<div class="oj-kpi-row oj-dept-kpis">${kpis.map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${k.value}</div><div class="oj-kpi-label">${k.label}</div></div>`).join("")}</div>
				<div class="oj-dept-grid-2">
					<div class="oj-panel"><h4>${OJ.t("التحاليل الأكثر طلباً", "Most Requested Tests")}</h4>
						<div class="oj-donut-legend">${(data.top_tests || []).map((r) => `<div class="oj-donut-row"><span class="oj-donut-bar" style="width:${Math.max(8, r.pct || 0)}%"></span><span>${OJ.esc(r.test_name)}</span><strong>${r.pct || 0}%</strong></div>`).join("")}</div>
					</div>
					<div class="oj-panel"><h4>${OJ.t("الأجهزة", "Devices")}</h4>${OJ.dataTable(
						[
							{ field: "device_name", label: OJ.t("الجهاز", "Device") },
							{ field: "status", label: OJ.t("الحالة", "Status") },
							{ field: "modality", label: OJ.t("النوع", "Type") },
						],
						deviceRows
					)}</div>
				</div>
				<div class="oj-panel" style="margin-top:16px">
					<h4>${OJ.t("تقارير جاهزة للطباعة", "Reports Ready to Print")}</h4>
					<div class="oj-table-wrap"><table class="oj-data-table"><thead><tr>
						<th>${OJ.t("رقم التقرير", "Report #")}</th>
						<th>${OJ.t("المريض", "Patient")}</th>
						<th>${OJ.t("نوع التحليل", "Panel")}</th>
						<th>${OJ.t("الحالة", "Status")}</th>
						<th>${OJ.t("إجراء", "Action")}</th>
					</tr></thead><tbody>${reportRows || `<tr><td colspan="5" class="oj-muted">${OJ.t("لا تقارير", "No reports")}</td></tr>`}</tbody></table></div>
				</div>
				<div class="oj-nav-actions">
					<button type="button" class="oj-btn oj-btn-outline" data-route="List/Healthcare Lab Sample">${OJ.t("عرض جميع العينات", "All samples")}</button>
					<button type="button" class="oj-btn oj-btn-primary" data-route="List/Healthcare Diagnostic Report">${OJ.t("جميع التقارير", "All reports")}</button>
				</div>
			`);
			$body.find("[data-route]").on("click", function () {
				OJ.navigateRoute($(this).attr("data-route"));
			});
			$body.find(".oj-print-lab").on("click", function () {
				printLabReport($(this).closest("tr").attr("data-report"));
			});
		},
		tabs: [
			{ id: "home", ar: "الرئيسية", en: "Home" },
			{ id: "worklist", ar: "قائمة العمل", en: "Worklist" },
			{ id: "stock", ar: "المخزون والعهدة", en: "Inventory" },
			{ id: "purchases", ar: "المشتريات", en: "Purchases" },
			{ id: "accounts", ar: "الحسابات", en: "Accounts" },
		],
		tableTitle: OJ.t("آخر العينات", "Latest Samples"),
		tableField: "recent_samples",
		tableColumns: [
			{ field: "name", label: OJ.t("رقم العينة", "Sample #") },
			{ field: "patient_display", label: OJ.t("المريض", "Patient") },
			{ field: "sample_type", label: OJ.t("النوع", "Type") },
			{ field: "status", label: OJ.t("الحالة", "Status") },
		],
		worklistColumns: [
			{ field: "name", label: OJ.t("العينة", "Sample") },
			{ field: "patient_display", label: OJ.t("المريض", "Patient") },
			{ field: "sample_type", label: OJ.t("النوع", "Type") },
			{ field: "status", label: OJ.t("الحالة", "Status") },
			{ field: "specimen_id", label: OJ.t("الباركود", "Barcode") },
		],
		worklistActionLabel: OJ.t("جمع العينة", "Collect"),
		onWorklistBind($body, _data, reload) {
			$body.find(".oj-wl-action").on("click", async function () {
				const id = $(this).closest("tr").attr("data-row-id");
				try {
					const r = await OJ.call("omnexa_healthcare.api.lab_desk.collect_lab_sample", { lab_sample: id });
					frappe.show_alert({
						message: `${OJ.t("تم جمع العينة", "Sample collected")}: ${r.specimen_id || ""}`,
						indicator: "green",
					});
					reload();
				} catch (e) {
					OJ.showCallError(e);
				}
			});
		},
	});
};
