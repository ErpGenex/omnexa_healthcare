/* global frappe */
(function () {
	const STORAGE_LANG = "hc_site_lang";
	const FEATURES = [
		{ icon: "🚑", ar: "طوارئ 24/7", en: "24/7 Emergency" },
		{ icon: "🏥", ar: "عيادات خارجية", en: "Outpatient Clinics" },
		{ icon: "📅", ar: "حجز سهل", en: "Easy Booking" },
		{ icon: "🔬", ar: "نتائج المختبر", en: "Lab Results" },
		{ icon: "⚕️", ar: "أحدث الأجهزة", en: "Latest Devices" },
		{ icon: "💙", ar: "رعاية عالية الجودة", en: "High-Quality Care" },
	];

	const SERVICE_VISUALS = {
		Emergency: "🚑",
		Laboratory: "🔬",
		Radiology: "📷",
		Pharmacy: "💊",
		default: "🏥",
	};

	window.HospitalSite = {
		config: null,
		lang: localStorage.getItem(STORAGE_LANG) || "ar",
		params: new URLSearchParams(window.location.search),

		init(page) {
			this.page = page;
			this.loadConfig().then(() => {
				this.applyTheme();
				this.renderChrome();
				if (typeof this[`init_${page}`] === "function") {
					this[`init_${page}`]();
				}
			});
		},

		t(key) {
			const map = {
				home: { ar: "الرئيسية", en: "Home" },
				doctors: { ar: "الأطباء", en: "Doctors" },
				departments: { ar: "الأقسام", en: "Departments" },
				booking: { ar: "حجز موعد", en: "Book Appointment" },
				shop: { ar: "المتجر", en: "Shop" },
				contact: { ar: "تواصل معنا", en: "Contact Us" },
				book_now: { ar: "احجز موعد", en: "Book Appointment" },
				contact_us: { ar: "تواصل معنا", en: "Contact Us" },
				our_departments: { ar: "الأقسام الطبية", en: "Medical Departments" },
				our_doctors: { ar: "فريق الأطباء", en: "Our Doctors" },
				featured_services: { ar: "خدمات مميزة", en: "Featured Services" },
				all: { ar: "الكل", en: "All" },
				years_exp: { ar: "سنوات خبرة", en: "years experience" },
				next: { ar: "التالي", en: "Next" },
				back: { ar: "السابق", en: "Back" },
				confirm: { ar: "تأكيد الحجز", en: "Confirm booking" },
				loading: { ar: "جاري التحميل...", en: "Loading..." },
			};
			return (map[key] && map[key][this.lang]) || key;
		},

		esc(value) {
			return frappe.utils.escape_html(value == null ? "" : String(value));
		},

		siteArgs() {
			const args = {};
			if (this.params.get("site")) args.site = this.params.get("site");
			if (this.params.get("company")) args.company = this.params.get("company");
			if (this.params.get("branch")) args.branch = this.params.get("branch");
			return args;
		},

		querySuffix(extra) {
			const q = new URLSearchParams(this.siteArgs());
			Object.entries(extra || {}).forEach(([k, v]) => {
				if (v != null && v !== "") q.set(k, v);
			});
			const s = q.toString();
			return s ? `?${s}` : "";
		},

		async loadConfig() {
			const r = await frappe.call({
				method: "omnexa_healthcare.api.public_hospital_site.get_site_config",
				args: this.siteArgs(),
			});
			this.config = r.message || {};
			if (this.config.primary_color) {
				document.documentElement.style.setProperty("--hc-primary", this.config.primary_color);
			}
		},

		applyTheme() {
			const root = document.querySelector(".hc-site");
			if (!root) return;
			root.dir = this.lang === "ar" ? "rtl" : "ltr";
			root.lang = this.lang;
		},

		nameField() {
			return this.lang === "ar" ? "hospital_name_ar" : "hospital_name_en";
		},

		textField(base) {
			return this.lang === "ar" ? `${base}_ar` : `${base}_en`;
		},

		toggleLang() {
			this.lang = this.lang === "ar" ? "en" : "ar";
			localStorage.setItem(STORAGE_LANG, this.lang);
			this.applyTheme();
			this.renderChrome();
			if (typeof this[`init_${this.page}`] === "function") {
				this[`init_${this.page}`]();
			}
		},

		renderChrome() {
			const cfg = this.config || {};
			const name = cfg[this.nameField()] || cfg.hospital_name_ar || "Hospital";
			const logo = cfg.logo ? `<img src="${this.esc(cfg.logo)}" alt="">` : "🏥";
			const suffix = this.querySuffix();
			const nav = [
				{ href: `/hospital${suffix}`, key: "home", page: "home" },
				{ href: `/hospital/doctors${suffix}`, key: "doctors", page: "doctors" },
				{ href: `/hospital/booking${suffix}`, key: "booking", page: "booking" },
			];
			if (cfg.features && cfg.features.shop) {
				nav.push({ href: `/hospital/shop${suffix}`, key: "shop", page: "shop" });
			}

			const header = document.getElementById("hc-header");
			if (header) {
				header.innerHTML = `
					<div class="hc-wrap hc-header-inner">
						<a class="hc-brand" href="/hospital${suffix}">${logo}<span>${this.esc(name)}</span></a>
						<button type="button" class="hc-mobile-toggle" id="hc-menu-toggle">☰</button>
						<nav class="hc-nav" id="hc-nav">
							${nav
								.map(
									(item) =>
										`<a href="${item.href}" class="${this.page === item.page ? "active" : ""}">${this.t(item.key)}</a>`
								)
								.join("")}
						</nav>
						<div class="hc-actions">
							<button type="button" class="hc-lang" id="hc-lang-toggle">${this.lang === "ar" ? "EN" : "AR"}</button>
							<a class="hc-btn hc-btn-primary" href="/hospital/booking${suffix}">${this.t("book_now")}</a>
						</div>
					</div>`;
				document.getElementById("hc-lang-toggle")?.addEventListener("click", () => this.toggleLang());
				document.getElementById("hc-menu-toggle")?.addEventListener("click", () => {
					document.getElementById("hc-nav")?.classList.toggle("open");
				});
			}

			const footer = document.getElementById("hc-footer");
			if (footer) {
				const contact = cfg.contact || {};
				footer.innerHTML = `
					<div class="hc-wrap hc-footer-grid">
						<div>
							<h3>${this.esc(name)}</h3>
							<p>${this.esc(cfg[this.textField("tagline")] || "")}</p>
							<p>${this.esc(contact[this.textField("address")] || "")}</p>
						</div>
						<div>
							<h4>${this.t("contact")}</h4>
							<p>${this.esc(contact.phone || "")}</p>
							<p>${this.esc(contact.email || "")}</p>
						</div>
						<div>
							<h4>${this.t("booking")}</h4>
							<p><a href="/hospital/booking${suffix}">${this.t("book_now")}</a></p>
							<p><a href="/hospital/doctors${suffix}">${this.t("doctors")}</a></p>
						</div>
					</div>`;
			}
		},

		async init_home() {
			const cfg = this.config;
			const suffix = this.querySuffix();
			const hero = document.getElementById("hc-home-hero");
			if (hero) {
				hero.innerHTML = `
					<div class="hc-wrap hc-hero-grid">
						<div>
							<h1>${this.esc(cfg[this.textField("tagline")] || "")}</h1>
							<h2 style="font-weight:500;margin:0 0 16px;">${this.esc(cfg[this.nameField()] || "")}</h2>
							<p>${this.esc(cfg[this.textField("hero_text")] || (this.lang === "ar" ? "مستشفى متكامل يقدم رعاية صحية شاملة بأحدث التقنيات الطبية." : "A full-service hospital delivering comprehensive care with modern medical technology."))}</p>
							<div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap;">
								<a class="hc-btn hc-btn-light" href="/hospital/booking${suffix}">${this.t("book_now")}</a>
								<a class="hc-btn hc-btn-outline" style="color:#fff;border-color:#fff;" href="#hc-contact">${this.t("contact_us")}</a>
							</div>
						</div>
						<div class="hc-hero-card">
							<h3>${this.lang === "ar" ? "لماذا نحن؟" : "Why choose us?"}</h3>
							<ul style="line-height:1.9;padding-${this.lang === "ar" ? "right" : "left"}:18px;">
								<li>${this.lang === "ar" ? "فريق طبي متخصص" : "Specialist medical team"}</li>
								<li>${this.lang === "ar" ? "حجز إلكتروني سريع" : "Fast online booking"}</li>
								<li>${this.lang === "ar" ? "خدمات تشخيصية متكاملة" : "Integrated diagnostics"}</li>
							</ul>
						</div>
					</div>`;
			}

			const featuresBar = document.getElementById("hc-features-bar");
			if (featuresBar) {
				featuresBar.innerHTML = FEATURES.map((f) =>
					`<div class="hc-feature-item"><span>${f.icon}</span>${this.lang === "ar" ? f.ar : f.en}</div>`
				).join("");
			}

			const stats = cfg.stats || {};
			const statsEl = document.getElementById("hc-stats");
			if (statsEl) {
				const items = [
					{ n: stats.departments, ar: "قسم طبي", en: "Departments" },
					{ n: stats.doctors, ar: "طبيب متخصص", en: "Doctors" },
					{ n: stats.patients, ar: "مريض سنوياً", en: "Annual patients" },
					{ n: stats.years, ar: "سنوات خبرة", en: "Years experience" },
				];
				statsEl.innerHTML = `<div class="hc-wrap hc-stats-grid">${items
					.map(
						(i) => `<div><div class="hc-stat-num">${this.esc(String(i.n || 0))}+</div><div class="hc-stat-label">${this.lang === "ar" ? i.ar : i.en}</div></div>`
					)
					.join("")}</div>`;
			}

			const deptWrap = document.getElementById("hc-departments");
			if (deptWrap) {
				deptWrap.innerHTML = `<div class="hc-empty">${this.t("loading")}</div>`;
				const r = await frappe.call({
					method: "omnexa_healthcare.api.public_hospital_site.get_published_departments",
					args: this.siteArgs(),
				});
				const rows = r.message || [];
				deptWrap.innerHTML = rows.length
					? `<div class="hc-grid-4">${rows
							.map(
								(d) => `<a class="hc-card hc-dept-card" href="/hospital/booking${this.querySuffix({ department: d.name })}">
									<div class="hc-dept-icon">${d.icon || "🏥"}</div>
									<h3>${this.esc(d.department_name)}</h3>
								</a>`
							)
							.join("")}</div>`
					: `<div class="hc-empty">${this.lang === "ar" ? "لا توجد أقسام منشورة." : "No published departments."}</div>`;
			}

			const servicesWrap = document.getElementById("hc-services");
			if (servicesWrap) {
				const r = await frappe.call({
					method: "omnexa_healthcare.api.web_booking.get_published_services",
					args: { company: cfg.company, branch: cfg.branch },
				});
				const rows = (r.message || []).slice(0, 4);
				servicesWrap.innerHTML = rows.length
					? `<div class="hc-grid-4">${rows
							.map((s) => {
								const icon = SERVICE_VISUALS[s.service_type] || SERVICE_VISUALS.default;
								return `<div class="hc-card hc-service-card">
									<div class="hc-service-img">${icon}</div>
									<h3>${this.esc(s.service_title)}</h3>
									<p class="text-muted">${this.esc(s.website_description || "")}</p>
									<a class="hc-btn hc-btn-light" href="/hospital/booking${this.querySuffix({ service: s.service_code })}">${this.t("book_now")}</a>
								</div>`;
							})
							.join("")}</div>`
					: "";
			}
		},

		async init_doctors() {
			const wrap = document.getElementById("hc-doctors-page");
			if (!wrap) return;
			wrap.innerHTML = `<div class="hc-empty">${this.t("loading")}</div>`;
			const r = await frappe.call({
				method: "omnexa_healthcare.api.public_hospital_site.get_published_doctors",
				args: this.siteArgs(),
			});
			const doctors = r.message || [];
			const specialties = [...new Set(doctors.map((d) => d.specialty_name).filter(Boolean))];
			let filter = "all";

			const render = () => {
				const filtered = filter === "all" ? doctors : doctors.filter((d) => d.specialty_name === filter);
				wrap.innerHTML = `
					<div class="hc-filters">
						<button type="button" class="hc-pill ${filter === "all" ? "active" : ""}" data-filter="all">${this.t("all")}</button>
						${specialties
							.map(
								(s) =>
									`<button type="button" class="hc-pill ${filter === s ? "active" : ""}" data-filter="${this.esc(s)}">${this.esc(s)}</button>`
							)
							.join("")}
					</div>
					<div class="hc-grid-3">${filtered
						.map(
							(d) => `<div class="hc-card hc-doctor-card">
								<div class="hc-doctor-photo">${d.photo ? `<img src="${this.esc(d.photo)}" alt="">` : "👨‍⚕️"}</div>
								<h3>${this.esc(d.practitioner_name)}</h3>
								<div>${this.esc(d.specialty_name || "")}</div>
								<div class="hc-rating">★ ${this.esc(String(d.rating || "4.8"))}</div>
								<div>${this.esc(String(d.years_of_experience || 5))} ${this.t("years_exp")}</div>
								<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix({ practitioner: d.name })}">${this.t("book_now")}</a>
							</div>`
						)
						.join("")}</div>`;
				wrap.querySelectorAll(".hc-pill").forEach((btn) => {
					btn.addEventListener("click", () => {
						filter = btn.dataset.filter;
						render();
					});
				});
			};
			render();
		},

		async init_booking() {
			const shell = document.getElementById("hc-booking-app");
			if (!shell) return;
			const cfg = this.config;
			const state = {
				step: 1,
				department: this.params.get("department") || "",
				practitioner: this.params.get("practitioner") || "",
				service_code: this.params.get("service") || "",
				date: new Date().toISOString().slice(0, 10),
				slot: null,
				patient: {},
			};

			const [deptsR, doctorsR, servicesR] = await Promise.all([
				frappe.call({ method: "omnexa_healthcare.api.public_hospital_site.get_published_departments", args: this.siteArgs() }),
				frappe.call({ method: "omnexa_healthcare.api.public_hospital_site.get_published_doctors", args: this.siteArgs() }),
				frappe.call({ method: "omnexa_healthcare.api.web_booking.get_published_services", args: { company: cfg.company, branch: cfg.branch } }),
			]);
			const departments = deptsR.message || [];
			const doctors = doctorsR.message || [];
			const services = servicesR.message || [];

			const steps = [
				this.lang === "ar" ? "اختر القسم" : "Department",
				this.lang === "ar" ? "اختر الطبيب" : "Doctor",
				this.lang === "ar" ? "اختر الموعد" : "Time",
				this.lang === "ar" ? "البيانات الشخصية" : "Personal info",
				this.lang === "ar" ? "تأكيد الحجز" : "Confirm",
			];

			const render = async () => {
				shell.innerHTML = `
					<div class="hc-steps">${steps
						.map(
							(label, idx) =>
								`<div class="hc-step ${state.step === idx + 1 ? "active" : ""} ${state.step > idx + 1 ? "done" : ""}">${idx + 1}. ${label}</div>`
						)
						.join("")}</div>
					<div class="hc-panel" id="hc-booking-panel"></div>
					<div style="display:flex;justify-content:space-between;margin-top:16px;">
						<button type="button" class="hc-btn hc-btn-outline" id="hc-book-back" ${state.step === 1 ? "disabled" : ""}>${this.t("back")}</button>
						<button type="button" class="hc-btn hc-btn-primary" id="hc-book-next">${state.step === 5 ? this.t("confirm") : this.t("next")}</button>
					</div>`;

				const panel = document.getElementById("hc-booking-panel");
				if (state.step === 1) {
					panel.innerHTML = `<div class="hc-grid-4">${departments
						.map(
							(d) =>
								`<button type="button" class="hc-card hc-dept-card" data-dept="${this.esc(d.name)}">
									<div class="hc-dept-icon">${d.icon || "🏥"}</div>
									<strong>${this.esc(d.department_name)}</strong>
								</button>`
						)
						.join("")}</div>`;
					panel.querySelectorAll("[data-dept]").forEach((btn) => {
						btn.addEventListener("click", () => {
							state.department = btn.dataset.dept;
							state.practitioner = "";
							state.service_code = "";
							btn.parentElement.querySelectorAll(".hc-card").forEach((c) => c.classList.remove("selected"));
							btn.classList.add("selected");
						});
					});
				} else if (state.step === 2) {
					const filtered = state.department
						? doctors.filter((d) => (d.service_codes || []).length || true)
						: doctors;
					panel.innerHTML = `<div class="hc-grid-3">${filtered
						.map(
							(d) => `<button type="button" class="hc-card hc-doctor-card" data-doc="${this.esc(d.name)}">
								<div class="hc-doctor-photo" style="height:140px;">${d.photo ? `<img src="${this.esc(d.photo)}">` : "👨‍⚕️"}</div>
								<strong>${this.esc(d.practitioner_name)}</strong>
								<div>${this.esc(d.specialty_name || "")}</div>
							</button>`
						)
						.join("")}</div>`;
					panel.querySelectorAll("[data-doc]").forEach((btn) => {
						btn.addEventListener("click", () => {
							state.practitioner = btn.dataset.doc;
							const doc = doctors.find((x) => x.name === state.practitioner);
							state.service_code = (doc && doc.service_codes && doc.service_codes[0]) || state.service_code;
							panel.querySelectorAll(".hc-card").forEach((c) => c.classList.remove("selected"));
							btn.classList.add("selected");
						});
					});
				} else if (state.step === 3) {
					panel.innerHTML = `
						<div class="hc-field" style="max-width:280px;margin-bottom:16px;">
							<label>${this.lang === "ar" ? "التاريخ" : "Date"}</label>
							<input type="date" id="hc-book-date" value="${this.esc(state.date)}">
						</div>
						<div class="hc-slot-grid" id="hc-slots">${this.t("loading")}</div>`;
					const loadSlots = async () => {
						state.date = document.getElementById("hc-book-date").value;
						const slotsEl = document.getElementById("hc-slots");
						slotsEl.innerHTML = this.t("loading");
						let slots = [];
						if (state.service_code) {
							const r = await frappe.call({
								method: "omnexa_healthcare.api.web_booking.get_booking_slots",
								args: {
									company: cfg.company,
									branch: cfg.branch,
									service_code: state.service_code,
									date: state.date,
								},
							});
							slots = (r.message && r.message.slots) || [];
							if (r.message && r.message.practitioner) state.practitioner = r.message.practitioner;
						} else if (state.practitioner) {
							const r = await frappe.call({
								method: "omnexa_healthcare.api.public_hospital_site.get_practitioner_booking_slots",
								args: { ...this.siteArgs(), practitioner: state.practitioner, date: state.date },
							});
							slots = (r.message && r.message.slots) || [];
						}
						slotsEl.innerHTML = slots.length
							? slots
									.map(
										(s) =>
											`<button type="button" class="hc-slot" data-start="${this.esc(s.start)}" data-end="${this.esc(s.end)}">${this.esc(String(s.start).slice(11, 16))}</button>`
									)
									.join("")
							: `<div class="hc-empty">${this.lang === "ar" ? "لا توجد مواعيد متاحة." : "No slots available."}</div>`;
						slotsEl.querySelectorAll(".hc-slot").forEach((btn) => {
							btn.addEventListener("click", () => {
								state.slot = { start: btn.dataset.start, end: btn.dataset.end };
								slotsEl.querySelectorAll(".hc-slot").forEach((b) => b.classList.remove("selected"));
								btn.classList.add("selected");
							});
						});
					};
					document.getElementById("hc-book-date").addEventListener("change", loadSlots);
					await loadSlots();
				} else if (state.step === 4) {
					panel.innerHTML = `
						<div class="hc-form-grid">
							<div class="hc-field"><label>${this.lang === "ar" ? "الاسم الأول" : "First name"}</label><input id="hc-given" value="${this.esc(state.patient.given_name || "")}"></div>
							<div class="hc-field"><label>${this.lang === "ar" ? "اسم العائلة" : "Last name"}</label><input id="hc-family" value="${this.esc(state.patient.family_name || "")}"></div>
							<div class="hc-field"><label>${this.lang === "ar" ? "الجوال" : "Phone"}</label><input id="hc-phone" value="${this.esc(state.patient.phone || "")}"></div>
							<div class="hc-field"><label>${this.lang === "ar" ? "البريد" : "Email"}</label><input id="hc-email" type="email" value="${this.esc(state.patient.email || "")}"></div>
						</div>`;
				} else if (state.step === 5) {
					const doc = doctors.find((d) => d.name === state.practitioner);
					panel.innerHTML = `
						<h3>${this.lang === "ar" ? "ملخص الحجز" : "Booking summary"}</h3>
						<ul style="line-height:2;">
							<li><b>${this.lang === "ar" ? "الطبيب" : "Doctor"}:</b> ${this.esc((doc && doc.practitioner_name) || state.practitioner)}</li>
							<li><b>${this.lang === "ar" ? "الموعد" : "Slot"}:</b> ${this.esc(state.slot ? `${state.slot.start} — ${state.slot.end}` : "")}</li>
							<li><b>${this.lang === "ar" ? "المريض" : "Patient"}:</b> ${this.esc(`${state.patient.given_name || ""} ${state.patient.family_name || ""}`.trim())}</li>
							<li><b>${this.lang === "ar" ? "الجوال" : "Phone"}:</b> ${this.esc(state.patient.phone || "")}</li>
						</ul>
						<div id="hc-book-result"></div>`;
				}

				document.getElementById("hc-book-back").addEventListener("click", () => {
					if (state.step > 1) {
						state.step -= 1;
						render();
					}
				});
				document.getElementById("hc-book-next").addEventListener("click", async () => {
					if (state.step === 4) {
						state.patient = {
							given_name: document.getElementById("hc-given").value.trim(),
							family_name: document.getElementById("hc-family").value.trim(),
							phone: document.getElementById("hc-phone").value.trim(),
							email: document.getElementById("hc-email").value.trim(),
						};
					}
					if (state.step === 5) {
						await this.submitBooking(state, cfg);
						return;
					}
					if (state.step === 1 && !state.department) {
						frappe.show_alert({ message: this.lang === "ar" ? "اختر القسم" : "Select department", indicator: "orange" });
						return;
					}
					if (state.step === 2 && !state.practitioner) {
						frappe.show_alert({ message: this.lang === "ar" ? "اختر الطبيب" : "Select doctor", indicator: "orange" });
						return;
					}
					if (state.step === 3 && !state.slot) {
						frappe.show_alert({ message: this.lang === "ar" ? "اختر الموعد" : "Select time slot", indicator: "orange" });
						return;
					}
					if (state.step === 4 && !(state.patient.given_name && state.patient.family_name && state.patient.phone)) {
						frappe.show_alert({ message: this.lang === "ar" ? "أكمل البيانات" : "Complete personal details", indicator: "orange" });
						return;
					}
					state.step += 1;
					render();
				});
			};

			if (!state.service_code && state.practitioner) {
				const doc = doctors.find((d) => d.name === state.practitioner);
				state.service_code = (doc && doc.service_codes && doc.service_codes[0]) || "";
			}
			render();
		},

		async submitBooking(state, cfg) {
			if (!state.service_code) {
				const services = (await frappe.call({
					method: "omnexa_healthcare.api.web_booking.get_published_services",
					args: { company: cfg.company, branch: cfg.branch },
				})).message || [];
				state.service_code = (services[0] && services[0].service_code) || "";
			}
			if (!state.service_code) {
				frappe.msgprint(this.lang === "ar" ? "لا توجد خدمة متاحة للحجز." : "No bookable service configured.");
				return;
			}
			try {
				const r = await frappe.call({
					method: "omnexa_healthcare.api.web_booking.book_appointment_online",
					args: {
						payload: {
							company: cfg.company,
							branch: cfg.branch,
							service_code: state.service_code,
							practitioner: state.practitioner,
							given_name: state.patient.given_name,
							family_name: state.patient.family_name,
							phone: state.patient.phone,
							email: state.patient.email,
							appointment_date: state.slot.start,
							slot_end: state.slot.end,
						},
					},
				});
				const msg = r.message || {};
				const el = document.getElementById("hc-book-result");
				if (el) {
					el.innerHTML = `<div class="alert alert-success">${this.lang === "ar" ? "تم الحجز بنجاح" : "Booking confirmed"}: <b>${this.esc(msg.name)}</b></div>`;
				}
			} catch (err) {
				frappe.msgprint((err && err.message) || "Booking failed");
			}
		},

		async init_shop() {
			const wrap = document.getElementById("hc-shop-page");
			if (!wrap) return;
			wrap.innerHTML = `<div class="hc-empty">${this.t("loading")}</div>`;
			const r = await frappe.call({
				method: "omnexa_healthcare.api.public_hospital_site.get_shop_items",
				args: this.siteArgs(),
			});
			const data = r.message || {};
			const services = data.services || [];
			const products = data.products || [];
			wrap.innerHTML = `
				<h2>${this.lang === "ar" ? "خدمات ومنتجات" : "Services & products"}</h2>
				<h3 style="margin-top:24px;">${this.lang === "ar" ? "الخدمات الطبية" : "Medical services"}</h3>
				<div class="hc-grid-3">${services
					.map(
						(s) => `<div class="hc-card">
							<h4>${this.esc(s.service_title)}</h4>
							<p>${this.esc(s.website_description || "")}</p>
							<div><b>${this.esc(String(s.default_rate || ""))}</b></div>
							<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix({ service: s.service_code })}">${this.t("book_now")}</a>
						</div>`
					)
					.join("")}</div>
				${
					products.length
						? `<h3 style="margin-top:32px;">${this.lang === "ar" ? "منتجات المتجر" : "Store products"}</h3>
				<div class="hc-grid-3">${products
					.map(
						(p) => `<div class="hc-card">
							<h4>${this.esc(this.lang === "ar" ? p.title_ar || p.title_en : p.title_en || p.title_ar)}</h4>
							<p>${this.esc(p.item_type || "")}</p>
						</div>`
					)
					.join("")}</div>`
						: ""
				}`;
		},
	};
})();
