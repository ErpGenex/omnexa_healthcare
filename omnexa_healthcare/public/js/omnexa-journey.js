/**
 * Omnexa Journey — World-class healthcare experience UI kit
 * Shared by Reception · Cashier · Physician · Patient portals
 */
/* global frappe */
(function (window) {
	"use strict";

	const STEPS_8 = [
		{ id: 1, ar: "اختيار العيادة", en: "Choose Clinic", icon: "🏥" },
		{ id: 2, ar: "اختيار الطبيب", en: "Choose Doctor", icon: "👨‍⚕️" },
		{ id: 3, ar: "بيانات المريض", en: "Patient Data", icon: "📋" },
		{ id: 4, ar: "تأكيد الحجز", en: "Confirm Booking", icon: "✓" },
		{ id: 5, ar: "إصدار التذكرة", en: "Visit Token", icon: "🎫" },
		{ id: 6, ar: "السداد", en: "Payment", icon: "💳" },
		{ id: 7, ar: "الدخول للعيادة", en: "Clinic Entry", icon: "🚪" },
		{ id: 8, ar: "الملف الطبي", en: "Medical File", icon: "📁" },
	];

	const PAY_METHODS = [
		{ id: "Card", ar: "بطاقة بنكية", en: "Bank Card", icon: "💳" },
		{ id: "Apple Pay", ar: "Apple Pay", en: "Apple Pay", icon: "" },
		{ id: "Wallet", ar: "محفظة إلكترونية", en: "E-Wallet", icon: "📱" },
		{ id: "Cash", ar: "نقدي", en: "Cash", icon: "💵" },
		{ id: "Insurance", ar: "تأمين", en: "Insurance", icon: "🛡️" },
	];

	function lang() {
		return (frappe.boot && frappe.boot.lang === "ar") || document.documentElement.lang === "ar" ? "ar" : "en";
	}

	function t(ar, en) {
		if (lang() === "en") {
			return en;
		}
		if (typeof __ === "function") {
			const translated = __(en);
			if (translated && translated !== en) {
				return translated;
			}
		}
		return ar;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function shell(options) {
		const { title, subtitle, role, kpis, sidebar, body, footer } = options;
		const isRtl = lang() === "ar";
		const $root = $(`<div class="oj-shell ${isRtl ? "oj-rtl" : "oj-ltr"}" dir="${isRtl ? "rtl" : "ltr"}"></div>`);
		const navItems = sidebar || [];
		const navHtml = navItems
			.map(
				(n) =>
					`<a class="oj-sidebar-item ${n.active ? "active" : ""}" href="${esc(n.route || "#")}" data-route="${esc(n.id || "")}"><span class="oj-sidebar-icon">${n.icon || "•"}</span><span>${esc(n.label)}</span></a>`
			)
			.join("");
		const kpiHtml = (kpis || [])
			.map(
				(k) =>
					`<div class="oj-kpi-card"><div class="oj-kpi-value">${esc(k.value)}</div><div class="oj-kpi-label">${esc(k.label)}</div></div>`
			)
			.join("");
		$root.html(`
			<aside class="oj-sidebar">${navHtml}<div class="oj-sidebar-spacer"></div><a class="oj-sidebar-item oj-logout" href="/app">⏻ ${t("خروج", "Logout")}</a></aside>
			<div class="oj-main">
				<header class="oj-topbar">
					<div class="oj-topbar-brand"><span class="oj-logo">+</span><div><strong>Omnexa Healthcare</strong><small>${esc(subtitle || "")}</small></div></div>
					<div class="oj-topbar-meta"><span class="oj-pill">${esc(role || "")}</span><span class="oj-datetime"></span><span class="oj-user">${esc(frappe.session.user_fullname || frappe.session.user)}</span></div>
				</header>
				<div class="oj-title-row"><h1>${esc(title || "")}</h1></div>
				${kpiHtml ? `<div class="oj-kpi-row">${kpiHtml}</div>` : ""}
				<div class="oj-body">${body || ""}</div>
				${footer ? `<footer class="oj-footer">${footer}</footer>` : ""}
			</div>
		`);
		const now = new Date();
		$root.find(".oj-datetime").text(now.toLocaleString(lang() === "ar" ? "ar-EG" : "en-GB"));
		return $root;
	}

	function stepper(current, total) {
		total = total || 8;
		const steps = STEPS_8.slice(0, total);
		let html = `<div class="oj-stepper">`;
		steps.forEach((s) => {
			const cls = s.id < current ? "done" : s.id === current ? "active" : "";
			html += `<div class="oj-step ${cls}"><div class="oj-step-ring">${s.id < current ? "✓" : s.id}</div><div class="oj-step-label">${esc(t(s.ar, s.en))}</div></div>`;
		});
		html += `</div>`;
		return html;
	}

	function clinicGrid(clinics, onSelect) {
		const $g = $(`<div class="oj-clinic-grid"></div>`);
		(clinics || []).forEach((c) => {
			const $card = $(`
				<div class="oj-clinic-card" data-id="${esc(c.id || c.specialty || c.department)}">
					<div class="oj-clinic-icon">${c.icon || "🏥"}</div>
					<h4>${esc(c.name || c.specialty_name || c.department_name)}</h4>
					<p class="oj-muted">${esc(c.subtitle || "")}</p>
					<div class="oj-clinic-stats">
						<span>👨‍⚕️ ${esc(c.doctor_count || 0)} ${t("أطباء", "doctors")}</span>
						<span>⏳ ${esc(c.waiting_count || 0)} ${t("منتظر", "waiting")}</span>
					</div>
					<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${t("اختيار", "Select")}</button>
				</div>
			`);
			$card.on("click", () => onSelect && onSelect(c));
			$g.append($card);
		});
		return $g;
	}

	function doctorGrid(doctors, onSelect) {
		const $g = $(`<div class="oj-doctor-grid"></div>`);
		(doctors || []).forEach((d) => {
			const $card = $(`
				<div class="oj-doctor-card">
					<div class="oj-doctor-avatar">${(d.name || d.practitioner_name || "?")[0]}</div>
					<h4>${esc(d.practitioner_name || d.name)}</h4>
					<p class="oj-muted">${esc(d.specialty_name || d.specialty || "")}</p>
					<div class="oj-rating">★ ${esc(d.rating || "4.9")}</div>
					<div class="oj-clinic-stats"><span>⏳ ${esc(d.queue_count || 0)}</span><span>🕐 ${esc(d.next_slot || t("اليوم", "Today"))}</span></div>
					<button type="button" class="oj-btn oj-btn-outline oj-btn-sm">${t("اختيار الطبيب", "Select")}</button>
				</div>
			`);
			$card.find("button, .oj-doctor-card").on("click", (e) => {
				e.stopPropagation();
				onSelect && onSelect(d);
			});
			$g.append($card);
		});
		return $g;
	}

	function visitTokenCard(token) {
		if (!token) return `<p class="oj-muted">${t("لا توجد تذكرة", "No token")}</p>`;
		return `
			<div class="oj-token-card">
				<div class="oj-token-header">${t("تذكرة الزيارة", "Visit Token")}</div>
				<div class="oj-token-id">${esc(token.appointment_id || token.name)}</div>
				<div class="oj-token-queue">${t("رقم الدور", "Queue")}: <strong>${esc(token.queue_number || "—")}</strong></div>
				<div class="oj-qr-placeholder" data-qr="${esc(token.qr_token || token.journey_token || "")}">QR</div>
				<p class="oj-muted oj-token-status">${esc(token.payment_status || token.status || "")}</p>
			</div>`;
	}

	function paymentMethods(selected, onSelect) {
		const $w = $(`<div class="oj-pay-grid"></div>`);
		PAY_METHODS.forEach((m) => {
			const $c = $(`<div class="oj-pay-card ${selected === m.id ? "selected" : ""}" data-method="${m.id}"><span>${m.icon}</span><strong>${esc(t(m.ar, m.en))}</strong></div>`);
			$c.on("click", () => onSelect && onSelect(m.id));
			$w.append($c);
		});
		return $w;
	}

	function physicianModules(data) {
		const d = data || {};
		const vitals = d.vitals || {};
		return `
			<div class="oj-emr-grid">
				<div class="oj-emr-card oj-emr-vitals">
					<h5>${t("ملخص المريض", "Patient Summary")}</h5>
					<div class="oj-vitals-row">
						<span>BP ${esc(vitals.bp || "—")}</span><span>HR ${esc(vitals.hr || "—")}</span>
						<span>T ${esc(vitals.temp || "—")}</span><span>W ${esc(vitals.weight || "—")}</span>
					</div>
					<p class="oj-muted">${esc(d.chronic_summary || "")}</p>
				</div>
				<div class="oj-emr-card"><h5>${t("التشخيص", "Diagnosis")}</h5><p>${esc(d.diagnosis || "—")}</p></div>
				<div class="oj-emr-card"><h5>${t("الروشتة", "ePrescription")}</h5><ul>${(d.medications || []).map((m) => `<li>${esc(m.medication_text || m.drug_name || m)}</li>`).join("") || `<li class="oj-muted">—</li>`}</ul></div>
				<div class="oj-emr-card"><h5>${t("الطلبات", "Orders")}</h5><ul>${(d.orders || []).map((o) => `<li>${esc(o.request_title || o)}</li>`).join("") || `<li class="oj-muted">—</li>`}</ul></div>
				<div class="oj-emr-card"><h5>${t("التحويل", "Referral")}</h5><p>${esc(d.referral || "—")}</p></div>
				<div class="oj-emr-card oj-emr-actions"><button class="oj-btn oj-btn-primary oj-save-encounter">${t("حفظ وإنهاء", "Save & Close")}</button></div>
			</div>`;
	}

	function loading() {
		return `<div class="oj-loading">${t("جاري التحميل...", "Loading...")}</div>`;
	}

	function registrationForm(data, opts) {
		const d = data || {};
		const o = opts || {};
		const showEmail = o.showEmail !== false;
		return `
			<div class="oj-form-grid oj-registration-form">
				<div class="oj-form-group"><label>${t("الاسم الأول", "First name")}</label><input class="oj-reg-given" value="${esc(d.given_name || "")}" required /></div>
				<div class="oj-form-group"><label>${t("اسم العائلة", "Last name")}</label><input class="oj-reg-family" value="${esc(d.family_name || "")}" required /></div>
				<div class="oj-form-group"><label>${t("الرقم القومي", "National ID")}</label><input class="oj-reg-nid" value="${esc(d.national_id || "")}" required /></div>
				<div class="oj-form-group"><label>${t("الجوال", "Mobile")}</label><input class="oj-reg-phone" value="${esc(d.phone || "")}" required /></div>
				${showEmail ? `<div class="oj-form-group"><label>${t("البريد", "Email")}</label><input class="oj-reg-email" type="email" value="${esc(d.email || "")}" required /></div>` : ""}
				<div class="oj-form-group"><label>${t("تاريخ الميلاد", "Birth date")}</label><input class="oj-reg-birth" type="date" value="${esc(d.birth_date || "")}" required /></div>
				<div class="oj-form-group"><label>${t("النوع", "Gender")}</label>
					<select class="oj-reg-gender"><option value="">${t("اختر", "Select")}</option>
					<option value="male" ${d.gender === "male" ? "selected" : ""}>${t("ذكر", "Male")}</option>
					<option value="female" ${d.gender === "female" ? "selected" : ""}>${t("أنثى", "Female")}</option></select></div>
				<div class="oj-form-group"><label>${t("المدينة", "City")}</label><input class="oj-reg-city" value="${esc(d.city || "")}" /></div>
			</div>`;
	}

	function readRegistrationForm($root) {
		return {
			given_name: ($root.find(".oj-reg-given").val() || "").trim(),
			family_name: ($root.find(".oj-reg-family").val() || "").trim(),
			national_id: ($root.find(".oj-reg-nid").val() || "").trim(),
			phone: ($root.find(".oj-reg-phone").val() || "").trim(),
			email: ($root.find(".oj-reg-email").val() || "").trim(),
			birth_date: ($root.find(".oj-reg-birth").val() || "").trim(),
			gender: ($root.find(".oj-reg-gender").val() || "").trim(),
			city: ($root.find(".oj-reg-city").val() || "").trim(),
		};
	}

	function otpPanel() {
		return `
			<div class="oj-otp-panel">
				<p class="oj-muted">${t("أدخل رمز التحقق المرسل لجوالك", "Enter OTP sent to your mobile")}</p>
				<div class="oj-form-group"><input class="oj-otp-code" placeholder="${t("6 أرقام", "6 digits")}" maxlength="6" /></div>
				<button type="button" class="oj-btn oj-btn-outline oj-resend-otp">${t("إعادة إرسال", "Resend")}</button>
			</div>`;
	}

	function call(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method,
				args: args || {},
				callback(r) {
					resolve(r.message);
				},
				error(err) {
					reject(err);
				},
			});
		});
	}

	function mountDeskPage(wrapper, title) {
		frappe.ui.make_app_page({ parent: wrapper, title: title, single_column: true });
		$(wrapper).find(".page-head").hide();
		return $(wrapper).find(".layout-main-section");
	}

	function ensureKit() {
		if (typeof shell !== "function") {
			frappe.msgprint(__("Omnexa Journey assets missing. Run: bench build --app omnexa_healthcare"));
			return false;
		}
		return true;
	}

	window.OmnexaJourney = {
		STEPS_8,
		PAY_METHODS,
		lang,
		t,
		esc,
		shell,
		stepper,
		clinicGrid,
		doctorGrid,
		visitTokenCard,
		paymentMethods,
		physicianModules,
		loading,
		registrationForm,
		readRegistrationForm,
		otpPanel,
		call,
		mountDeskPage,
		ensureKit,
		defaultSidebar(role) {
			const base = [
				{ id: "reception", label: t("الاستقبال", "Reception"), icon: "🏥", route: "/app/healthcare-reception-desk", active: role === "reception" },
				{ id: "cashier", label: t("الخزينة", "Cashier"), icon: "💰", route: "/app/healthcare-cashier-desk", active: role === "cashier" },
				{ id: "physician", label: t("الطبيب", "Physician"), icon: "👨‍⚕️", route: "/app/healthcare-physician-workbench", active: role === "physician" },
				{ id: "queue", label: t("الطابور", "Queue"), icon: "📋", route: "/app/healthcare-patient-queue" },
				{ id: "chart", label: t("الملف الطبي", "Chart"), icon: "📁", route: "/app/healthcare-patient-chart" },
				{ id: "patient", label: t("بوابة المريض", "Patient Portal"), icon: "👤", route: "/app/healthcare-patient-consumer" },
			];
			return base;
		},
	};
})(window);
