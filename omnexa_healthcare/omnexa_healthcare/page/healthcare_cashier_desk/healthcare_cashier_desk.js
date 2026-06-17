frappe.pages["healthcare-cashier-desk"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const company = frappe.defaults.get_user_default("Company");
	const branch = frappe.defaults.get_user_default("Branch");
	const $mount = OJ.mountDeskPage(wrapper, __("Cashier Desk"));
	let selectedAppt = null;
	let payMethod = "Cash";

	async function loadQueue($list) {
		$list.html(OJ.loading());
		const rows = await OJ.call("omnexa_healthcare.api.journey_desk.get_cashier_queue", { company, branch });
		$list.empty();
		if (!rows.length) {
			$list.html(`<p class="oj-muted">${OJ.t("لا توجد مدفوعات معلقة", "No pending payments")}</p>`);
			return;
		}
		const html = [`<table class="table table-bordered table-sm"><thead><tr>
			<th>${OJ.t("المريض", "Patient")}</th><th>${OJ.t("الطبيب", "Doctor")}</th><th>${OJ.t("المبلغ", "Amount")}</th><th></th>
		</tr></thead><tbody>`];
		rows.forEach((r) => {
			html.push(`<tr data-appt="${OJ.esc(r.name)}"><td>${OJ.esc(r.patient_display || r.patient)}</td><td>${OJ.esc(r.specialty)}</td><td>${r.amount_due}</td>
				<td><button class="oj-btn oj-btn-sm oj-btn-outline oj-select-pay">${OJ.t("سداد", "Pay")}</button></td></tr>`);
		});
		html.push("</tbody></table>");
		$list.html(html.join(""));
		$list.find(".oj-select-pay").on("click", function () {
			selectedAppt = $(this).closest("tr").data("appt");
			$(".oj-pay-section").show();
		});
	}

	async function render() {
		const kpis = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_kpis", { company, branch });
		const $body = $(`
			<div class="oj-panel">
				<h4>${OJ.t("طابور السداد", "Payment Queue")}</h4>
				<div class="oj-queue-list"></div>
			</div>
			<div class="oj-panel oj-pay-section" style="display:none">
				<h4>${OJ.t("طريقة الدفع", "Payment Method")}</h4>
				<div class="oj-pay-mount"></div>
				<button class="oj-btn oj-btn-success oj-complete-pay">${OJ.t("تأكيد السداد", "Confirm Payment")}</button>
			</div>
		`);
		const $shell = OJ.shell({
			title: OJ.t("الخزينة — سداد الزيارات", "Cashier — Visit Payments"),
			subtitle: OJ.t("Treasury Desk", "Treasury Desk"),
			role: OJ.t("أمين الخزينة", "Cashier"),
			kpis: [
				{ value: kpis.revenue_today, label: OJ.t("محصل اليوم", "Collected Today") },
				{ value: kpis.appointments_today, label: OJ.t("مواعيد", "Appointments") },
			],
			sidebar: OJ.defaultSidebar("cashier"),
			body: "",
		});
		$shell.find(".oj-body").append($body);
		$mount.empty().append($shell);
		const $pay = $body.find(".oj-pay-mount");
		$pay.append(OJ.paymentMethods(payMethod, (m) => { payMethod = m; $pay.empty().append(OJ.paymentMethods(payMethod, arguments.callee)); }));
		loadQueue($body.find(".oj-queue-list"));
		$body.find(".oj-complete-pay").on("click", async () => {
			if (!selectedAppt) return frappe.msgprint(OJ.t("اختر موعداً", "Select appointment"));
			await OJ.call("omnexa_healthcare.api.journey_desk.record_cashier_payment", { appointment: selectedAppt, payment_method: payMethod });
			frappe.show_alert({ message: OJ.t("تم السداد", "Paid"), indicator: "green" });
			selectedAppt = null;
			$(".oj-pay-section").hide();
			loadQueue($body.find(".oj-queue-list"));
		});
	}

	render();
};
