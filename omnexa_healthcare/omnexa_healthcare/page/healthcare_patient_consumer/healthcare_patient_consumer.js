frappe.pages["healthcare-patient-consumer"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const state = {
		step: 0,
		clinic: null,
		doctor: null,
		patient: null,
		sessionToken: null,
		registration: {},
		booking: null,
		token: null,
		payMethod: "Card",
	};
	const company = frappe.defaults.get_user_default("Company");
	const branch = frappe.defaults.get_user_default("Branch");
	const $mount = OJ.mountDeskPage(wrapper, __("My Health"));
	$(wrapper).addClass("oj-patient-journey");

	async function render() {
		const $content = $(`<div></div>`);
		const stepperIdx = state.step <= 0 ? 0 : state.step <= 2 ? state.step : state.step + 1;
		if (state.step > 0) $content.append(OJ.stepper(stepperIdx));
		const $panel = $(`<div class="oj-panel"></div>`).appendTo($content);

		if (state.step === 0) {
			$panel.html(`
				<h4>${OJ.t("تسجيل الدخول / حساب جديد", "Login / New Account")}</h4>
				<p class="oj-muted">${OJ.t("التسجيل الكامل إلزامي قبل الحجز", "Full registration required before booking")}</p>
				<div class="oj-tabs" style="display:flex;gap:8px;margin-bottom:12px">
					<button class="oj-btn oj-btn-primary oj-tab-reg">${OJ.t("حساب جديد", "Register")}</button>
					<button class="oj-btn oj-btn-outline oj-tab-login">${OJ.t("دخول OTP", "OTP Login")}</button>
				</div>
				<div class="oj-reg-block">${OJ.registrationForm(state.registration, { showEmail: true })}</div>
				<div class="oj-login-block" style="display:none">
					<div class="oj-form-group"><label>${OJ.t("الجوال", "Mobile")}</label><input class="oj-login-phone" /></div>
					<button class="oj-btn oj-btn-outline oj-send-login-otp">${OJ.t("إرسال OTP", "Send OTP")}</button>
				</div>
				<div class="oj-otp-block" style="display:none;margin-top:12px">${OJ.otpPanel()}</div>
				<div style="margin-top:12px"><button class="oj-btn oj-btn-primary oj-reg-submit">${OJ.t("تسجيل وإرسال OTP", "Register & Send OTP")}</button></div>
			`);
			$panel.find(".oj-tab-reg").on("click", () => {
				$panel.find(".oj-reg-block,.oj-reg-submit").show();
				$panel.find(".oj-login-block").hide();
			});
			$panel.find(".oj-tab-login").on("click", () => {
				$panel.find(".oj-reg-block,.oj-reg-submit").hide();
				$panel.find(".oj-login-block").show();
			});
			$panel.find(".oj-reg-submit").on("click", async () => {
				const payload = { ...OJ.readRegistrationForm($panel), company, branch };
				const res = await OJ.call("omnexa_healthcare.api.web_booking.register_for_booking", { payload });
				state.patient = { name: res.patient, patient_name: res.patient_name };
				state.registration = payload;
				$panel.find(".oj-otp-block").show();
				if (res.demo_otp) frappe.show_alert({ message: `OTP: ${res.demo_otp}`, indicator: "blue" });
			});
			$panel.find(".oj-send-login-otp").on("click", async () => {
				const mobile = $panel.find(".oj-login-phone").val();
				await OJ.call("omnexa_healthcare.api.patient_registration.login_patient_otp", { mobile });
				$panel.find(".oj-otp-block").show();
			});
			$panel.find(".oj-otp-block").on("click", ".oj-resend-otp", async () => {
				const mobile = state.registration.phone || $panel.find(".oj-login-phone").val();
				await OJ.call("omnexa_healthcare.api.patient_otp.send_patient_otp", { mobile, patient: state.patient && state.patient.name });
			});
			$panel.find(".oj-otp-block").on("input", ".oj-otp-code", async function () {
				if (String($(this).val()).length !== 6) return;
				const mobile = state.registration.phone || $panel.find(".oj-login-phone").val();
				const res = await OJ.call("omnexa_healthcare.api.web_booking.verify_for_booking", {
					mobile,
					otp: $(this).val(),
					patient: state.patient.name,
				});
				state.sessionToken = res.session_token;
				state.step = 1;
				render();
			});
		} else if (state.step === 1) {
			$panel.html(OJ.loading());
			const clinics = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_clinics", { company, branch });
			$panel.empty().append(`<h4>${OJ.t("اختيار العيادة", "Choose Clinic")}</h4>`);
			$panel.append(OJ.clinicGrid(clinics, (c) => { state.clinic = c; state.step = 2; render(); }));
		} else if (state.step === 2) {
			const doctors = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_doctors", { company, branch, specialty: state.clinic.specialty });
			$panel.html(`<h4>${OJ.t("اختيار الطبيب", "Choose Doctor")}</h4>`);
			$panel.append(OJ.doctorGrid(doctors, (d) => { state.doctor = d; state.step = 3; render(); }));
		} else if (state.step === 3) {
			$panel.html(`
				<h4>${OJ.t("تأكيد الحجز", "Confirm")}</h4>
				<p>${OJ.esc(state.patient.patient_name)} · ${OJ.esc(state.doctor.practitioner_name)}</p>
				<button class="oj-btn oj-btn-primary oj-book">${OJ.t("تأكيد الحجز", "Confirm booking")}</button>
			`);
			$panel.find(".oj-book").on("click", async () => {
				const now = frappe.datetime.now_datetime();
				const patientId = state.patient.name || state.patient.patient;
				const res = await OJ.call("omnexa_healthcare.api.journey_desk.create_reception_booking", {
					patient: patientId,
					practitioner: state.doctor.name,
					company,
					branch,
					specialty: state.clinic.specialty,
					appointment_date: now,
					booking_fee: 300,
					session_token: state.sessionToken,
				});
				state.booking = res;
				state.token = res;
				state.step = 4;
				render();
			});
		} else if (state.step === 4) {
			$panel.html(`<h4>${OJ.t("تذكرة الزيارة", "Visit Token")}</h4>${OJ.visitTokenCard(state.token)}<button class="oj-btn oj-btn-primary oj-pay-step">${OJ.t("السداد", "Pay")}</button>`);
			OJ.bindVisitTokenCard($panel, state.token);
			$panel.find(".oj-pay-step").on("click", () => { state.step = 5; render(); });
		} else if (state.step === 5) {
			const $pay = OJ.paymentMethods(state.payMethod, (m) => { state.payMethod = m; render(); });
			$panel.html(`<h4>${OJ.t("السداد", "Payment")}</h4>`).append($pay);
			$panel.append(`<button class="oj-btn oj-btn-success oj-do-pay">${OJ.t("ادفع الآن", "Pay now")}</button>`);
			$panel.find(".oj-do-pay").on("click", async () => {
				await OJ.call("omnexa_healthcare.api.journey_desk.record_cashier_payment", { appointment: state.token.name, payment_method: state.payMethod });
				state.step = 6;
				render();
			});
		} else if (state.step === 6) {
			$panel.html(`
				<h4>${OJ.t("الدخول للعيادة", "Clinic Entry")}</h4>
				<div class="oj-token-card"><div class="oj-qr-placeholder">✓</div><p>${OJ.t("تم السداد — امسح QR عند الباب", "Paid — scan QR at clinic door")}</p></div>
				<button class="oj-btn oj-btn-primary oj-file">${OJ.t("الملف الطبي", "Medical file")}</button>
			`);
			$panel.find(".oj-file").on("click", () => { state.step = 7; render(); });
		} else {
			const chart = await OJ.call("omnexa_healthcare.api.journey_desk.get_physician_workbench", { patient: state.patient.name });
			$panel.html(`<h4>${OJ.t("ملخص الملف الطبي", "Medical File Summary")}</h4>${OJ.physicianModules(chart)}`);
		}

		const journeySteps = state.step <= 0 ? 0 : state.step <= 2 ? state.step : state.step + 1;
		if (state.step > 0) $content.find(".oj-stepper .oj-step").each(function (i) {
			$(this).toggleClass("active", i + 1 === journeySteps).toggleClass("done", i + 1 < journeySteps);
		});

		const $shell = OJ.shell({
			title: OJ.t("بوابة المريض — Omnexa Journey", "Patient Portal — Omnexa Journey"),
			subtitle: OJ.t("سجّل · احجز · ادفع · تابع ملفك", "Register · Book · Pay · Track"),
			role: OJ.t("مريض", "Patient"),
			sidebar: OJ.defaultSidebar("patient"),
			bodyEl: $content,
		});
		$mount.empty().append($shell);
	}

	render();
};
