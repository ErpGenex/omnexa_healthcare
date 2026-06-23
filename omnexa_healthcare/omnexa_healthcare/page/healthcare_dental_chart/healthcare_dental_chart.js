frappe.pages["healthcare-dental-chart"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	const DD = omnexa_healthcare.department;
	if (!OJ || !DD || !DD.mount) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare"));
		return;
	}

	DD.mount(wrapper, {
		deskTitle: __("Dental Clinic Desk"),
		titleAr: "عيادة الأسنان",
		titleEn: "Dental Clinic Desk",
		roleAr: "عيادة الأسنان",
		roleEn: "Dental Clinic",
		sidebarRole: "dental",
		homeRoute: "/app/healthcare-workcenter",
		api: "omnexa_healthcare.api.dental_desk.get_dental_desk_dashboard",
		lessonApi: "omnexa_healthcare.api.dental_desk.complete_dental_lesson",
		defaultTab: "home",
		extraArgs(state) {
			return { patient: state.patient, academic_year: state.academicYear };
		},
		showDevices: false,
		chartTitle: OJ.t("توزيع الحالات العلاجية", "Treatment Cases"),
		chartField: "case_breakdown",
		chartLabelField: "label",
		tableTitle: OJ.t("ملخص العيادة", "Clinic Summary"),
		tableField: "teeth",
		tableColumns: [
			{ field: "tooth_id", label: OJ.t("السن", "Tooth") },
			{ field: "label_ar", label: OJ.t("الاسم", "Name") },
			{ field: "condition", label: OJ.t("الحالة", "Condition") },
		],
		kpiMap(k) {
			return [
				{ value: k.total_patients || 0, label: OJ.t("إجمالي المرضى", "Total Patients") },
				{ value: k.today_appointments || 0, label: OJ.t("مواعيد اليوم", "Today's Appointments") },
				{ value: k.active_cases || 0, label: OJ.t("حالات نشطة", "Active Cases"), hint: OJ.t("تحت العلاج", "Under treatment") },
				{ value: k.today_procedures || 0, label: OJ.t("إجراءات اليوم", "Today's Procedures") },
			];
		},
		homeRightHtml(data) {
			const withLessons = (data.teeth || []).filter((t) => t.has_lessons);
			const rows = withLessons
				.slice(0, 8)
				.map(
					(t) =>
						`<div class="oj-lesson-stat"><strong>${OJ.esc(t.tooth_id)}</strong> ${OJ.esc(t.label_ar)} <span class="oj-muted">(${t.lessons.length})</span></div>`
				)
				.join("");
			return `<div class="oj-panel"><h4>${OJ.t("دروس السنة الحالية", "Current Year Lessons")}</h4>${rows || `<p class="oj-muted">${OJ.t("اختر سنة من تبويب المخطط", "Pick a year in Chart tab")}</p>`}</div>`;
		},
		renderHome($body, data, state) {
			const kpis = [
				{ value: (data.kpis || {}).total_patients || 0, label: OJ.t("إجمالي المرضى", "Total Patients") },
				{ value: (data.kpis || {}).today_appointments || 0, label: OJ.t("مواعيد اليوم", "Today's Appointments") },
				{ value: (data.kpis || {}).active_cases || 0, label: OJ.t("حالات نشطة", "Active Cases") },
				{ value: (data.kpis || {}).today_procedures || 0, label: OJ.t("إجراءات اليوم", "Today's Procedures") },
			];
			$body.html(`
				<div class="oj-kpi-row oj-dept-kpis">${kpis.map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${k.value}</div><div class="oj-kpi-label">${k.label}</div></div>`).join("")}</div>
				<div class="oj-dept-grid-2">
					<div class="oj-panel"><h4>${OJ.t("توزيع الحالات", "Case Mix")}</h4>
						<div class="oj-donut-legend">${(data.case_breakdown || []).map((r) => `<div class="oj-donut-row"><span class="oj-donut-bar" style="width:${Math.max(8, r.pct || 0)}%"></span><span>${OJ.esc(r.label)}</span><strong>${r.pct || 0}%</strong></div>`).join("")}</div>
					</div>
					<div class="oj-panel oj-dental-legend-panel">
						<h4>${OJ.t("دليل الألوان", "Color Key")}</h4>
						<ul class="oj-dental-legend">
							<li><span class="oj-legend-dot available"></span>${OJ.t("دروس متاحة", "Available lessons")}</li>
							<li><span class="oj-legend-dot selected"></span>${OJ.t("السن المحدد", "Selected tooth")}</li>
							<li><span class="oj-legend-dot completed"></span>${OJ.t("مكتمل", "Completed")}</li>
							<li><span class="oj-legend-dot locked"></span>${OJ.t("بدون درس", "No lesson")}</li>
						</ul>
						<button type="button" class="oj-btn oj-btn-primary oj-goto-chart">${OJ.t("فتح المخطط التفاعلي", "Open Interactive Chart")}</button>
					</div>
				</div>
			`);
			$body.find(".oj-goto-chart").on("click", () => {
				state.tab = "chart";
				$(".oj-dept-tabs .oj-tab-btn[data-tab=chart]").trigger("click");
			});
		},
		tabs: [
			{ id: "home", ar: "الرئيسية", en: "Home" },
			{ id: "chart", ar: "المخطط التفاعلي", en: "Chart" },
			{ id: "stock", ar: "المخزون", en: "Inventory" },
			{ id: "purchases", ar: "المشتريات", en: "Purchases" },
			{ id: "accounts", ar: "الحسابات", en: "Accounts" },
		],
	});
};
