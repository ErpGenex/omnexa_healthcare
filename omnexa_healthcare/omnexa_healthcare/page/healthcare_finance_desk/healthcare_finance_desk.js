frappe.pages["healthcare-finance-desk"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, __("RCM Workcenter"));

	async function render() {
		const data = await OJ.call("omnexa_healthcare.api.journey_role_desks.get_cfo_dashboard", { company, branch });
		const kpiCards = [
			{ value: data.revenue_today, label: OJ.t("إيراد اليوم", "Revenue Today") },
			{ value: data.paid_today, label: OJ.t("مسدد اليوم", "Paid Today") },
			{ value: data.unpaid_charges || 0, label: OJ.t("رسوم Draft", "Draft Charges") },
			{ value: data.unpaid_invoices, label: OJ.t("مواعيد غير مسددة", "Unpaid Appts") },
			{ value: data.physician_ledger_open || 0, label: OJ.t("استحقاقات أطباء", "Physician Accruals") },
			{ value: data.physician_settlements_draft || 0, label: OJ.t("تسويات معلقة", "Pending Settlements") },
		];

		const $body = $(`<div class="healthcare-rcm-workcenter"></div>`);

		$body.append(`<h4 class="oj-section-title">${OJ.t("💼 فوترة المرضى والحسابات", "Patient Billing & Accounts")}</h4>`);
		$body.append(
			OJ.linkGrid([
				{ label: OJ.t("سجل المرضى", "Patient Registry"), icon: "👤", route: "List/Healthcare Patient" },
				{ label: OJ.t("رسوم الخدمة", "Service Charges"), icon: "💳", route: "List/Healthcare Service Charge" },
				{ label: OJ.t("فواتير المرضى", "Patient Invoices"), icon: "🧾", route: "List/Sales Invoice" },
				{ label: OJ.t("مدفوعات المرضى", "Patient Payments"), icon: "💵", route: "List/Payment Entry" },
				{ label: OJ.t("الخزينة", "Cashier Desk"), icon: "🏦", route: "/app/healthcare-cashier-desk" },
				{ label: OJ.t("حسابات ERP", "Patient ERP Accounts"), icon: "📒", route: "List/Customer" },
				{ label: OJ.t("رسوم الكشف", "Consultation Fees"), icon: "📋", route: "List/Healthcare Consultation Fee Rule" },
				{ label: OJ.t("أسعار الخدمات", "Service Catalog"), icon: "🏷️", route: "List/Healthcare Service Catalog" },
				{ label: OJ.t("تغطية التأمين", "Patient Coverage"), icon: "🛡️", route: "List/Healthcare Patient Coverage" },
			])
		);

		$body.append(`<h4 class="oj-section-title" style="margin-top:20px">${OJ.t("👨‍⚕️ إيرادات الأطباء والمحاسبة", "Physician Revenue & Compensation")}</h4>`);
		if (!data.compensation_enabled) {
			$body.append(
				`<p class="oj-muted">${OJ.t(
					"محرك محاسبة الأطباء غير مفعّل — فعّله من Healthcare Settings",
					"Physician compensation engine is disabled — enable it in Healthcare Settings"
				)}</p>`
			);
		}
		$body.append(
			OJ.linkGrid([
				{ label: OJ.t("ملفات الأطباء", "Practitioner Profiles"), icon: "👨‍⚕️", route: "List/Healthcare Practitioner" },
				{ label: OJ.t("قواعد المحاسبة", "Compensation Rules"), icon: "⚖️", route: "List/Healthcare Physician Compensation Rule" },
				{ label: OJ.t("دفتر الطبيب", "Physician Ledger"), icon: "📘", route: "List/Healthcare Physician Ledger Entry" },
				{ label: OJ.t("تسويات الأطباء", "Settlements"), icon: "✅", route: "List/Healthcare Physician Settlement" },
				{ label: OJ.t("منصة الطبيب", "Physician Workbench"), icon: "🩺", route: "/app/healthcare-physician-workbench" },
				{ label: OJ.t("قيود GL", "GL Journal"), icon: "📗", route: "List/Journal Entry" },
				{ label: OJ.t("إعدادات النظام", "Healthcare Settings"), icon: "⚙️", route: "Form/Healthcare Settings/Healthcare Settings" },
			])
		);

		$body.append(`<h4 class="oj-section-title" style="margin-top:20px">${OJ.t("فواتير اليوم", "Today's Service Charges")}</h4>`);
		const chargeRows = (data.invoices || []).map((r) => ({ ...r, _actions: r.name }));
		const $chargeTable = $(`<div class="oj-charge-table"></div>`);
		$body.append($chargeTable);
		const rows = chargeRows || [];
		if (!rows.length) {
			$chargeTable.html(`<p class="oj-muted">${OJ.t("لا رسوم", "No charges")}</p>`);
		} else {
			const body = rows
				.map(
					(r) => `<tr>
					<td>${OJ.esc(r.name)}</td>
					<td>${OJ.esc(r.patient_name || r.patient)}</td>
					<td>${OJ.esc(r.total_amount)}</td>
					<td>${OJ.esc(r.status)}</td>
					<td><button class="oj-btn oj-btn-sm oj-btn-primary oj-inv-charge" data-name="${OJ.esc(r.name)}" ${r.status !== "Draft" ? "disabled" : ""}>${OJ.t("فاتورة", "Invoice")}</button></td>
				</tr>`
				)
				.join("");
			$chargeTable.html(`<table class="oj-data-table"><thead><tr>
				<th>${OJ.t("المرجع", "Ref")}</th><th>${OJ.t("المريض", "Patient")}</th>
				<th>${OJ.t("المبلغ", "Amount")}</th><th>${OJ.t("الحالة", "Status")}</th><th></th>
			</tr></thead><tbody>${body}</tbody></table>`);
			$chargeTable.find(".oj-inv-charge").on("click", async function () {
				const res = await OJ.call("omnexa_healthcare.api.billing.create_sales_invoice_from_service_charge", {
					service_charge: $(this).attr("data-name"),
				});
				frappe.show_alert({ message: OJ.t("فاتورة", "Invoice") + ": " + res.name, indicator: "green" });
				render();
			});
		}

		$body.append(`<h4 style="margin-top:16px">${OJ.t("إيراد حسب العيادة", "Revenue by Specialty")}</h4>`);
		$body.append(
			OJ.dataTable(
				[
					{ field: "specialty", label: OJ.t("العيادة", "Specialty") },
					{ field: "revenue", label: OJ.t("الإيراد", "Revenue") },
				],
				data.specialty_revenue || []
			)
		);

		$body.append(`<h4 style="margin-top:16px">${OJ.t("مطالبات التأمين", "Insurance Claims")}</h4>`);
		const claims = data.insurance_claims || [];
		if (!claims.length) {
			$body.append(`<p class="oj-muted">${OJ.t("لا مطالبات", "No claims")}</p>`);
		} else {
			const cbody = claims
				.map(
					(c) => `<tr>
					<td>${OJ.esc(c.name)}</td><td>${OJ.esc(c.payer)}</td><td>${OJ.esc(c.status)}</td>
					<td>${OJ.esc(c.claim_amount ?? c.claimed_amount ?? "—")}</td>
					<td><button class="oj-btn oj-btn-sm oj-btn-outline oj-claim-submit" data-name="${OJ.esc(c.name)}">${OJ.t("إرسال", "Submit")}</button></td>
				</tr>`
				)
				.join("");
			const $ct = $(`<table class="oj-data-table"><thead><tr>
				<th>${OJ.t("المطالبة", "Claim")}</th><th>${OJ.t("الجهة", "Payer")}</th>
				<th>${OJ.t("الحالة", "Status")}</th><th>${OJ.t("المبلغ", "Amount")}</th><th></th>
			</tr></thead><tbody>${cbody}</tbody></table>`);
			$body.append($ct);
			$ct.find(".oj-claim-submit").on("click", async function () {
				await OJ.call("omnexa_healthcare.api.rcm.submit_insurance_claim", { name: $(this).attr("data-name") });
				render();
			});
		}

		const $shell = OJ.shell({
			title: OJ.t("مركز إدارة الإيرادات — RCM", "RCM Workcenter"),
			subtitle: OJ.t("فوترة المرضى · محاسبة الأطباء · التأمين", "Patient Billing · Physician Revenue · Insurance"),
			role: OJ.t("مدير مالي", "CFO"),
			kpis: kpiCards,
			sidebar: OJ.defaultSidebar("finance"),
			bodyEl: $body,
			currentPage: "healthcare-finance-desk",
		});
		$mount.empty().append($shell);
	}

	render().catch((err) => OJ.showCallError(err));
};
