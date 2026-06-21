frappe.pages["healthcare-reception-desk"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) {
		frappe.msgprint(__("Load Omnexa Journey assets: bench build --app omnexa_healthcare"));
		return;
	}
	const state = { step: 1, clinic: null, doctor: null, patient: null, appointment: null, token: null, regMode: "search", bookingSlot: null };
	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, __("Reception Desk"));

	async function render() {
		const kpis = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_kpis", { company, branch });
		const todayAppts = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_today_appointments", { company, branch });
		const kpiCards = [
			{ value: kpis.appointments_today, label: OJ.t("مواعيد اليوم", "Appointments Today") },
			{ value: kpis.new_patients_today, label: OJ.t("مرضى جدد", "New Patients") },
			{ value: kpis.revenue_today, label: OJ.t("الإيراد (EGP)", "Revenue (EGP)") },
			{ value: kpis.avg_wait_mins + " " + OJ.t("د", "min"), label: OJ.t("متوسط الانتظار", "Avg Wait") },
		];
		const $body = $(`<div></div>`);
		const apptRows = (todayAppts || []).map((a) => ({
			name: a.name,
			patient_display: a.patient_display || a.patient,
			practitioner: a.practitioner,
			appointment_date: a.appointment_date,
			status: a.status,
			payment_status: a.payment_status,
		}));
		$body.append(`<div class="oj-panel oj-reception-appts" style="margin-bottom:16px">
			<h4>${OJ.t("مواعيد اليوم", "Today's Appointments")} (${apptRows.length})</h4>
			${OJ.dataTable(
				[
					{ field: "name", label: OJ.t("الموعد", "Appointment") },
					{ field: "patient_display", label: OJ.t("المريض", "Patient") },
					{ field: "practitioner", label: OJ.t("الطبيب", "Doctor") },
					{ field: "appointment_date", label: OJ.t("الوقت", "Time") },
					{ field: "status", label: OJ.t("الحالة", "Status") },
					{ field: "payment_status", label: OJ.t("السداد", "Payment") },
				],
				apptRows
			)}
			<button type="button" class="oj-btn oj-btn-sm oj-btn-outline oj-open-appts" style="margin-top:8px">${OJ.t("كل المواعيد", "All Appointments")}</button>
		</div>`);
		$body.find(".oj-open-appts").on("click", () => frappe.set_route("healthcare-appointments-desk"));
		$body.append(OJ.stepper(state.step));
		const $panel = $(`<div class="oj-panel"></div>`).appendTo($body);

		if (state.step === 1) {
			$panel.html(OJ.loading());
			const clinics = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_clinics", { company, branch });
			$panel.empty().append(`<h4>${OJ.t("اختيار العيادة", "Choose Clinic")}</h4>`);
			if (!clinics.length) {
				$panel.append(`<p class="oj-muted">${OJ.t("لا توجد عيادات لهذا الفرع", "No clinics for this branch")}</p>`);
			} else {
				$panel.append(OJ.clinicGrid(clinics, (c) => { state.clinic = c; state.step = 2; render(); }));
			}
		} else if (state.step === 2) {
			$panel.html(OJ.loading());
			const doctors = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_doctors", {
				company, branch, specialty: state.clinic.specialty,
			});
			$panel.empty().append(`<h4>${OJ.t("اختيار الطبيب", "Choose Doctor")}</h4>`);
			$panel.append(OJ.doctorGrid(doctors, (d) => { state.doctor = d; state.step = 3; render(); }));
		} else if (state.step === 3) {
			const mode = state.regMode || "search";
			$panel.html(`
				<h4>${OJ.t("بيانات المريض", "Patient Data")}</h4>
				<div style="display:flex;gap:8px;margin-bottom:12px">
					<button class="oj-btn ${mode === "search" ? "oj-btn-primary" : "oj-btn-outline"} oj-mode-search">${OJ.t("بحث", "Search")}</button>
					<button class="oj-btn ${mode === "new" ? "oj-btn-primary" : "oj-btn-outline"} oj-mode-new">${OJ.t("مريض جديد", "New Patient")}</button>
				</div>
				<div class="oj-search-panel" ${mode === "new" ? 'style="display:none"' : ""}>
					${OJ.patientSearchBar ? OJ.patientSearchBar() : ""}
					<p class="oj-muted" style="margin-top:8px">${OJ.t("ابحث بالاسم أو الرقم القومي أو رقم الجوال", "Search by name, national ID, or mobile number")}</p>
				</div>
				<div class="oj-new-panel" ${mode === "search" ? 'style="display:none"' : ""}>
					${OJ.registrationForm({}, { showEmail: false })}
					<button class="oj-btn oj-btn-success oj-create-patient" style="margin-top:12px">${OJ.t("تسجيل (<30 ث)", "Register (<30s)")}</button>
				</div>
				<div class="oj-nav-actions"><button class="oj-btn oj-btn-outline oj-back">${OJ.t("رجوع", "Back")}</button></div>
			`);
			$panel.find(".oj-mode-search").on("click", () => { state.regMode = "search"; render(); });
			$panel.find(".oj-mode-new").on("click", () => { state.regMode = "new"; render(); });
			if (OJ.bindPatientSearch) {
				OJ.bindPatientSearch(
					$panel.find(".oj-search-panel"),
					(row) => {
						state.patient = {
							name: row.name || row.patient,
							patient: row.patient || row.name,
							patient_name: row.patient_name || row.full_name || row.patient_display,
						};
						state.step = 4;
						render();
					},
					branch,
					company
				);
			}
			$panel.find(".oj-create-patient").on("click", async () => {
				const res = await OJ.call("omnexa_healthcare.api.journey_desk.quick_register_patient", {
					payload: { ...OJ.readRegistrationForm($panel), company, branch },
				});
				state.patient = { name: res.patient, patient_name: res.patient_name };
				state.step = 4;
				render();
			});
			$panel.find(".oj-back").on("click", () => { state.step = 2; render(); });
		} else if (state.step === 4) {
			$panel.html(OJ.loading());
			const date = frappe.datetime.get_today();
			const slots = await OJ.call("omnexa_healthcare.api.journey_desk.get_reception_booking_slots", {
				practitioner: state.doctor.name,
				branch,
				specialty: state.clinic.specialty,
				date,
			});
			if (!state.bookingSlot && slots.length) {
				state.bookingSlot = slots[0];
			}
			const slotOptions = (slots || [])
				.map(
					(s, i) =>
						`<button type="button" class="oj-btn oj-btn-sm ${state.bookingSlot && state.bookingSlot.start === s.start ? "oj-btn-primary" : "oj-btn-outline"} oj-pick-slot" data-idx="${i}" style="margin:4px">${OJ.esc(String(s.start).slice(11, 16))}${s.walk_in ? " *" : ""}</button>`
				)
				.join("");
			$panel.empty().append(`
				<h4>${OJ.t("تأكيد الحجز", "Confirm Booking")}</h4>
				<p><strong>${OJ.t("المريض", "Patient")}:</strong> ${OJ.esc(state.patient.patient_name)}</p>
				<p><strong>${OJ.t("الطبيب", "Doctor")}:</strong> ${OJ.esc(state.doctor.practitioner_name)}</p>
				<p><strong>${OJ.t("العيادة", "Clinic")}:</strong> ${OJ.esc(state.clinic.name)}</p>
				<div style="margin:12px 0">
					<strong>${OJ.t("الموعد", "Appointment")}:</strong>
					<div style="margin-top:8px">${slotOptions || `<span class="oj-muted">${OJ.t("حجز افتراضي اليوم", "Default walk-in today")}</span>`}</div>
				</div>
				<div class="oj-nav-actions">
					<button class="oj-btn oj-btn-outline oj-back">${OJ.t("رجوع", "Back")}</button>
					<button class="oj-btn oj-btn-primary oj-confirm">${OJ.t("تأكيد وإصدار تذكرة", "Confirm & Issue Token")}</button>
				</div>
			`);
			$panel.find(".oj-pick-slot").on("click", function () {
				const idx = parseInt($(this).attr("data-idx"), 10);
				state.bookingSlot = slots[idx];
				render();
			});
			$panel.find(".oj-back").on("click", () => { state.step = 3; render(); });
			$panel.find(".oj-confirm").on("click", async () => {
				try {
					const patientId = state.patient.name || state.patient.patient;
					if (!patientId) {
						return frappe.msgprint(OJ.t("اختر مريضاً", "Select a patient"));
					}
					const slot = state.bookingSlot || (slots && slots[0]);
					const res = await OJ.call("omnexa_healthcare.api.journey_desk.create_reception_booking", {
						patient: patientId,
						practitioner: state.doctor.name,
						company, branch,
						specialty: state.clinic.specialty,
						appointment_date: (slot && slot.start) || frappe.datetime.now_datetime(),
						slot_end: slot && slot.end,
						booking_fee: state.doctor.consultation_fee || 300,
					});
					state.token = res;
					state.step = 5;
					render();
				} catch (e) {
					OJ.showCallError(e);
				}
			});
		} else {
			$panel.html(`
				<h4>${OJ.t("تذكرة الزيارة", "Visit Token")}</h4>
				${OJ.visitTokenCard(state.token)}
				<div class="oj-nav-actions">
					<button class="oj-btn oj-btn-primary oj-to-pay">${OJ.t("السداد", "Payment")}</button>
					<button class="oj-btn oj-btn-outline oj-new">${OJ.t("مريض جديد", "New Patient")}</button>
				</div>
			`);
			OJ.bindVisitTokenCard($panel, state.token);
			$panel.find(".oj-to-pay").on("click", () => frappe.set_route("healthcare-cashier-desk"));
			$panel.find(".oj-new").on("click", () => {
				Object.assign(state, { step: 1, clinic: null, doctor: null, patient: null, appointment: null, token: null });
				render();
			});
		}

		const $shell = OJ.shell({
			title: OJ.t("رحلة المريض — الاستقبال", "Patient Journey — Reception"),
			subtitle: OJ.t("Omnexa Healthcare", "Omnexa Healthcare"),
			role: OJ.t("موظف استقبال", "Receptionist"),
			kpis: kpiCards,
			sidebar: OJ.defaultSidebar("reception"),
			bodyEl: $body,
			homeRoute: "/app/healthcare-demo-hub",
		});
		$mount.empty().append($shell);
	}

	render().catch((e) => OJ.showCallError(e));
};
