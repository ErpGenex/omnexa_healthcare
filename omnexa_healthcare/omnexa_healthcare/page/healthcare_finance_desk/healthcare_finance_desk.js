frappe.pages["healthcare-finance-desk"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, __("Finance Desk"));

	async function render() {
		const data = await OJ.call("omnexa_healthcare.api.journey_role_desks.get_cfo_dashboard", { company, branch });
		const kpiCards = [
			{ value: data.revenue_today, label: OJ.t("إيراد اليوم", "Revenue Today") },
			{ value: data.expenses_today, label: OJ.t("مصروفات", "Expenses") },
			{ value: data.unpaid_invoices, label: OJ.t("مواعيد غير مسددة", "Unpaid Appts") },
			{ value: data.unpaid_charges || 0, label: OJ.t("رسوم Draft", "Draft Charges") },
			{ value: data.paid_today, label: OJ.t("مسدد اليوم", "Paid Today") },
		];
		const $body = $(`<div></div>`);
		$body.append(
			OJ.linkGrid([
				{ label: OJ.t("رسوم الخدمة", "Service Charges"), icon: "💳", route: "List/Healthcare Service Charge" },
				{ label: OJ.t("المواعيد", "Appointments"), icon: "📅", route: "/app/healthcare-appointments-desk" },
				{ label: OJ.t("الخزينة", "Cashier Desk"), icon: "💰", route: "/app/healthcare-cashier-desk" },
			])
		);
		$body.append(`<h4>${OJ.t("فواتير اليوم", "Today's Service Charges")}</h4>`);
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
			title: OJ.t("المكتب المالي — المستشفى", "Hospital Finance Desk"),
			subtitle: OJ.t("Omnexa Healthcare", "Omnexa Healthcare"),
			role: OJ.t("مدير مالي", "CFO"),
			kpis: kpiCards,
			sidebar: OJ.defaultSidebar("finance"),
			bodyEl: $body,
		});
		$mount.empty().append($shell);
	}

	render().catch((err) => OJ.showCallError(err));
};
