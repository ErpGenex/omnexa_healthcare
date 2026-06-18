/**
 * Integrated department desk shell — lab, radiology, dental (Journey design system)
 */
frappe.provide("omnexa_healthcare.department");

omnexa_healthcare.department.mount = function (wrapper, config) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare"));
		return;
	}
	const { company, branch } = OJ.resolveCompanyBranch();
	const state = {
		tab: config.defaultTab || "home",
		data: null,
		patient: null,
		academicYear: 1,
		selectedTooth: null,
		selectedLesson: null,
		highlightTeeth: [],
	};
	const $mount = OJ.mountDeskPage(wrapper, config.deskTitle || config.titleEn);

	function money(v) {
		return (parseFloat(v || 0) || 0).toFixed(2);
	}

	function tabBtn(id, label) {
		const cls = state.tab === id ? "oj-btn-primary" : "oj-btn-outline";
		return `<button type="button" class="oj-btn ${cls} oj-tab-btn" data-tab="${id}">${label}</button>`;
	}

	function renderDonutLegend(rows, labelField) {
		if (!rows || !rows.length) return `<p class="oj-muted">${OJ.t("لا بيانات", "No data")}</p>`;
		return `<div class="oj-donut-legend">${rows
			.map(
				(r) =>
					`<div class="oj-donut-row"><span class="oj-donut-bar" style="width:${Math.max(8, r.pct || 0)}%"></span><span>${OJ.esc(r[labelField] || r.modality || r.test_name || r.label)}</span><strong>${r.pct || 0}%</strong></div>`
			)
			.join("")}</div>`;
	}

	function renderKpis(kpis) {
		return (kpis || [])
			.map(
				(k) =>
					`<div class="oj-kpi-card"><div class="oj-kpi-value">${OJ.esc(k.value)}</div><div class="oj-kpi-label">${OJ.esc(k.label)}</div>${k.hint ? `<div class="oj-muted" style="font-size:0.8rem">${OJ.esc(k.hint)}</div>` : ""}</div>`
			)
			.join("");
	}

	function renderHome($body, data) {
		if (config.renderHome) {
			config.renderHome($body, data, state, reload);
			return;
		}
		const kpis = config.kpiMap(data.kpis || {});
		const deviceRows = (data.devices || []).map((d) => ({
			...d,
			modality: d.modality || d.protocol || "—",
		}));
		const rightPanel =
			config.showDevices === false
				? config.homeRightHtml
					? config.homeRightHtml(data)
					: ""
				: `<div class="oj-panel"><h4>${OJ.t("الأجهزة", "Devices")}</h4>${OJ.dataTable(
						[
							{ field: "device_name", label: OJ.t("الجهاز", "Device") },
							{ field: "status", label: OJ.t("الحالة", "Status") },
							{ field: "modality", label: OJ.t("النوع", "Type") },
						],
						deviceRows
					)}</div>`;
		$body.html(`
			<div class="oj-kpi-row oj-dept-kpis">${renderKpis(kpis)}</div>
			<div class="oj-dept-grid-2">
				<div class="oj-panel"><h4>${OJ.esc(config.chartTitle)}</h4>${renderDonutLegend(data[config.chartField] || [], config.chartLabelField)}</div>
				${rightPanel}
			</div>
			<div class="oj-panel" style="margin-top:16px"><h4>${OJ.esc(config.tableTitle)}</h4>${OJ.dataTable(config.tableColumns, data[config.tableField] || [])}</div>
			${config.homeFooterHtml ? config.homeFooterHtml(data) : ""}
		`);
		bindRouteButtons($body);
	}

	function bindRouteButtons($root) {
		$root.find("[data-route]").on("click", function () {
			OJ.navigateRoute($(this).attr("data-route"));
		});
	}

	function renderWorklist($body, data) {
		const rows = data.worklist || [];
		const actionCol = config.worklistActionLabel
			? `<th>${OJ.esc(config.worklistActionLabel)}</th>`
			: "";
		const bodyRows = rows
			.map((row) => {
				const cells = (config.worklistColumns || [])
					.map((c) => `<td>${OJ.esc(row[c.field] ?? "—")}</td>`)
					.join("");
				const action = config.worklistActionLabel
					? `<td><button type="button" class="oj-btn oj-btn-sm oj-btn-primary oj-wl-action" data-id="${OJ.esc(row.name)}">${OJ.esc(config.worklistActionLabel)}</button></td>`
					: "";
				return `<tr data-row-id="${OJ.esc(row.name)}">${cells}${action}</tr>`;
			})
			.join("");
		$body.html(`
			<div class="oj-panel"><h4>${OJ.t("قائمة العمل", "Worklist")}</h4>
			<div class="oj-table-wrap"><table class="oj-data-table oj-worklist-table"><thead><tr>${(config.worklistColumns || []).map((c) => `<th>${OJ.esc(c.label)}</th>`).join("")}${actionCol}</tr></thead><tbody>${bodyRows || `<tr><td colspan="${(config.worklistColumns || []).length + (actionCol ? 1 : 0)}" class="oj-muted">${OJ.t("لا بيانات", "No data")}</td></tr>`}</tbody></table></div></div>`);
		if (config.onWorklistBind) config.onWorklistBind($body, data, reload);
		bindRouteButtons($body);
	}

	function renderStock($body, data) {
		$body.html(`
			<div class="oj-panel"><h4>${OJ.t("المخزون والعهدة", "Inventory & Custody")}</h4>
			<p class="oj-muted">${OJ.t("المخزن", "Warehouse")}: <strong>${OJ.esc(data.warehouse || "—")}</strong></p>
			${OJ.dataTable(
				[
					{ field: "item_name", label: OJ.t("الصنف", "Item") },
					{ field: "item_code", label: OJ.t("الكود", "Code") },
					{ field: "on_hand", label: OJ.t("المتوفر", "On Hand") },
				],
				data.stock_rows || []
			)}
			<h5 style="margin-top:16px">${OJ.t("تنبيهات النواقص", "Low Stock")}</h5>
			${OJ.alertList(
				(data.par_alerts || []).map((a) => ({
					level: "warning",
					text: `${a.item || a.item_code} — ${a.on_hand}/${a.par_level}`,
				}))
			)}</div>`);
	}

	function renderPurchases($body, data) {
		const p = data.purchases || {};
		$body.html(`
			<div class="oj-panel"><h4>${OJ.t("المشتريات", "Purchases")}</h4>
			${OJ.dataTable(
				[
					{ field: "name", label: OJ.t("أمر الشراء", "PO") },
					{ field: "supplier", label: OJ.t("المورد", "Supplier") },
					{ field: "status", label: OJ.t("الحالة", "Status") },
					{ field: "grand_total", label: OJ.t("الإجمالي", "Total") },
				],
				p.purchase_orders || []
			)}
			<h5 style="margin-top:16px">${OJ.t("استلام مخزني", "Stock Receipts")}</h5>
			${OJ.dataTable(
				[
					{ field: "name", label: OJ.t("المرجع", "Ref") },
					{ field: "posting_date", label: OJ.t("التاريخ", "Date") },
					{ field: "purpose", label: OJ.t("الغرض", "Purpose") },
				],
				p.stock_entries || []
			)}</div>`);
	}

	function renderAccounts($body, data) {
		const a = data.accounts || {};
		$body.html(`
			<div class="oj-panel"><h4>${OJ.t("الحسابات والتحصيل", "Accounts")}</h4>
			<div class="oj-kpi-row">
				<div class="oj-kpi-card"><div class="oj-kpi-value">${money(a.revenue_today)}</div><div class="oj-kpi-label">${OJ.t("إيراد اليوم", "Revenue Today")}</div></div>
			</div>
			<h5>${OJ.t("فواتير المبيعات", "Sales Invoices")}</h5>
			${OJ.dataTable(
				[
					{ field: "name", label: OJ.t("الفاتورة", "Invoice") },
					{ field: "customer", label: OJ.t("العميل", "Customer") },
					{ field: "grand_total", label: OJ.t("الإجمالي", "Total") },
					{ field: "status", label: OJ.t("الحالة", "Status") },
				],
				a.sales_invoices || []
			)}</div>`);
	}

	function renderDentalChart($body, data) {
		const chart = window.omnexa_healthcare && omnexa_healthcare.dentalChart;
		if (!chart || !chart.render) {
			$body.html(`<p class="oj-muted">${OJ.t("أعد بناء الأصول", "Rebuild assets")}: bench build --app omnexa_healthcare</p>`);
			return;
		}
		chart.render($body, data, state, {
			branch,
			onPatient(row) {
				state.patient = row.patient || row.name;
				reload();
			},
			onYear(year) {
				state.academicYear = year;
				state.selectedTooth = null;
				state.selectedLesson = null;
				state.highlightTeeth = [];
				reload();
			},
			onLesson(id, teeth) {
				state.selectedLesson = id;
				state.highlightTeeth = teeth || [];
				if (teeth && teeth.length === 1) state.selectedTooth = String(teeth[0]);
				renderTabBody($(".oj-dept-tab-body"));
			},
			onTooth(tid) {
				state.selectedTooth = String(tid);
				renderTabBody($(".oj-dept-tab-body"));
			},
			onShowAllLessons() {
				state.selectedLesson = null;
				state.highlightTeeth = (data.year_lessons || []).flatMap((l) => l.teeth || []);
				renderTabBody($(".oj-dept-tab-body"));
			},
			async onCompleteLesson(lessonId) {
				if (!state.patient || !state.selectedTooth) return;
				try {
					await OJ.call(config.lessonApi, {
						patient: state.patient,
						tooth_id: state.selectedTooth,
						lesson_id: lessonId,
						company,
						branch,
					});
					frappe.show_alert({ message: OJ.t("تم إكمال الدرس", "Lesson completed"), indicator: "green" });
					reload();
				} catch (e) {
					OJ.showCallError(e);
				}
			},
		});
	}

	function renderTabBody($tabBody) {
		const data = state.data || {};
		if (state.tab === "home") renderHome($tabBody, data);
		else if (state.tab === "worklist") renderWorklist($tabBody, data);
		else if (state.tab === "stock") renderStock($tabBody, data);
		else if (state.tab === "purchases") renderPurchases($tabBody, data);
		else if (state.tab === "accounts") renderAccounts($tabBody, data);
		else if (state.tab === "chart" && config.renderChart) config.renderChart($tabBody, data, state, reload);
		else if (state.tab === "chart") renderDentalChart($tabBody, data);
	}

	function switchTab(tab) {
		state.tab = tab;
		$(".oj-dept-tabs .oj-tab-btn").removeClass("oj-btn-primary").addClass("oj-btn-outline");
		$(`.oj-dept-tabs .oj-tab-btn[data-tab="${tab}"]`).removeClass("oj-btn-outline").addClass("oj-btn-primary");
		renderTabBody($(".oj-dept-tab-body"));
	}

	async function reload() {
		const args = Object.assign({ company, branch }, config.apiArgs || {}, config.extraArgs ? config.extraArgs(state) : {});
		state.data = await OJ.call(config.api, args);
		const k = state.data.kpis || {};
		const $shell = OJ.shell({
			title: OJ.t(config.titleAr, config.titleEn),
			subtitle: OJ.t("Omnexa Healthcare", "Omnexa Healthcare"),
			role: OJ.t(config.roleAr, config.roleEn),
			kpis: config.kpiMap(k).slice(0, 4),
			sidebar: OJ.defaultSidebar(config.sidebarRole || "nurse"),
			bodyEl: (() => {
				const $body = $('<div class="oj-dept-layout"></div>');
				const $tabs = $('<div class="oj-filter-bar oj-dept-tabs"></div>').appendTo($body);
				(config.tabs || []).forEach((t) => $tabs.append(tabBtn(t.id, OJ.t(t.ar, t.en))));
				$('<div class="oj-dept-tab-body"></div>').appendTo($body);
				$tabs.find(".oj-tab-btn").on("click", function () {
					switchTab($(this).attr("data-tab"));
				});
				return $body;
			})(),
			homeRoute: config.homeRoute || "/app/healthcare-demo-hub",
		});
		$mount.empty().append($shell);
		renderTabBody($shell.find(".oj-dept-tab-body"));
	}

	reload().catch((e) => OJ.showCallError(e));
};
