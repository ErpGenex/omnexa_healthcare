/* global frappe */
(function () {
	const STORAGE_LANG = "hc_site_lang";
	const FEATURE_SVGS = {
		care: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-4.5-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.5-7 10-7 10z"/></svg>',
		device: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 20h8"/></svg>',
		booking: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
		lab: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6v5l5 9a4 4 0 0 1-3.5 6H7.5A4 4 0 0 1 4 17l5-9V3z"/></svg>',
		clinic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M6 21V7l6-4 6 4v14"/><path d="M9 11h6v6H9z"/></svg>',
		emergency: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 4v6c0 5-3.5 8-8 8s-8-3-8-8V7l8-4z"/><path d="M12 8v4M10 10h4"/></svg>',
	};
	const FEATURES = [
		{ key: "care", ar: "رعاية عالية الجودة", en: "High-Quality Care" },
		{ key: "device", ar: "أحدث الأجهزة الطبية", en: "Latest Medical Equipment" },
		{ key: "booking", ar: "حجز موعد بسهولة", en: "Easy Appointment Booking" },
		{ key: "lab", ar: "نتائج التحاليل", en: "Lab Results" },
		{ key: "clinic", ar: "عيادات خارجية", en: "Outpatient Clinics" },
		{ key: "emergency", ar: "طوارئ 24 ساعة", en: "24-Hour Emergency" },
	];

	const SERVICE_IMAGES = {
		Emergency: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=800&q=80",
		Laboratory: "https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&w=800&q=80",
		Radiology: "https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=800&q=80",
		Pharmacy: "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=800&q=80",
		default: "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=800&q=80",
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
				clinics: { ar: "العيادات", en: "Clinics" },
				about: { ar: "من نحن", en: "About" },
				book_now_cta: { ar: "احجز موعد الآن", en: "Book Appointment Now" },
				featured_services_sub: { ar: "كل ما تحتاجه تحت سقف واحد", en: "Everything you need under one roof" },
				dept_sub: { ar: "تخصصات طبية متكاملة لرعايتكم", en: "Integrated medical specialties for your care" },
				doctors_sub: { ar: "نخبة من الأطباء المتخصصين لرعايتكم", en: "A selection of specialized doctors for your care" },
				booking_sub: { ar: "اختر موعدك المناسب بسهولة", en: "Choose your suitable appointment easily" },
				view_all_doctors: { ar: "عرض جميع الأطباء", en: "View all doctors" },
				working_hours: { ar: "أوقات العمل", en: "Working hours" },
				services_offered: { ar: "الخدمات المقدمة", en: "Services provided" },
				book_clinic: { ar: "احجز موعد في العيادة", en: "Book clinic appointment" },
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
				step_department: { ar: "اختر القسم", en: "Department" },
				step_doctor: { ar: "اختر الطبيب", en: "Doctor" },
				step_time: { ar: "اختر الموعد", en: "Time" },
				step_personal: { ar: "البيانات الشخصية", en: "Personal info" },
				step_confirm: { ar: "تأكيد الحجز", en: "Confirm" },
				choose_department: { ar: "اختر القسم الطبي", en: "Choose medical department" },
				date: { ar: "التاريخ", en: "Date" },
				no_slots: { ar: "لا توجد مواعيد متاحة.", en: "No slots available." },
				first_name: { ar: "الاسم الأول", en: "First name" },
				last_name: { ar: "اسم العائلة", en: "Last name" },
				phone: { ar: "الجوال", en: "Phone" },
				email: { ar: "البريد", en: "Email" },
				booking_summary: { ar: "ملخص الحجز", en: "Booking summary" },
				doctor: { ar: "الطبيب", en: "Doctor" },
				slot: { ar: "الموعد", en: "Slot" },
				patient: { ar: "المريض", en: "Patient" },
				select_department: { ar: "اختر القسم", en: "Select department" },
				select_doctor: { ar: "اختر الطبيب", en: "Select doctor" },
				no_doctors: { ar: "لا يوجد أطباء منشورون لهذا القسم.", en: "No published doctors for this department." },
				select_slot: { ar: "اختر الموعد", en: "Select time slot" },
				complete_personal: { ar: "أكمل البيانات", en: "Complete personal details" },
				booking_success: { ar: "تم الحجز بنجاح", en: "Booking confirmed" },
				no_service: { ar: "لا توجد خدمة متاحة للحجز.", en: "No bookable service configured." },
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
			this.syncTenantUrl();
			if (this.config.primary_color) {
				document.documentElement.style.setProperty("--hc-primary", this.config.primary_color);
			}
		},

		syncTenantUrl() {
			const cfg = this.config || {};
			const url = new URL(window.location.href);
			let changed = false;
			if (cfg.site_slug && !url.searchParams.get("site")) {
				url.searchParams.set("site", cfg.site_slug);
				changed = true;
			} else if (!url.searchParams.get("site") && !url.searchParams.get("company") && cfg.company) {
				url.searchParams.set("company", cfg.company);
				if (cfg.branch) url.searchParams.set("branch", cfg.branch);
				changed = true;
			}
			if (changed) {
				window.history.replaceState({}, "", url);
				this.params = url.searchParams;
			}
		},

		applyTheme() {
			const root = document.querySelector(".hc-site");
			if (!root) return;
			root.dir = this.lang === "ar" ? "rtl" : "ltr";
			root.lang = this.lang;
			root.classList.add("hc-alhayat");
		},

		featuredServiceTypes() {
			return ["Pharmacy", "Radiology", "Laboratory", "Emergency"];
		},

		pickFeaturedServices(rows) {
			const order = this.featuredServiceTypes();
			const picked = [];
			order.forEach((type) => {
				const row = rows.find((s) => s.service_type === type);
				if (row) picked.push(row);
			});
			if (picked.length < 4) {
				rows.forEach((s) => {
					if (picked.length < 4 && !picked.includes(s)) picked.push(s);
				});
			}
			return picked.slice(0, 4);
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
			const logo = cfg.logo
				? `<img src="${this.esc(cfg.logo)}" alt="" onerror="this.replaceWith(document.createTextNode('🏥'))">`
				: "🏥";
			const suffix = this.querySuffix();
			const nav = [
				{ href: `/hospital${suffix}`, key: "home", page: "home" },
				{ href: `/hospital${suffix}#hc-departments-section`, key: "departments", page: "home" },
				{ href: `/hospital/doctors${suffix}`, key: "doctors", page: "doctors" },
				{ href: `/hospital/booking${suffix}`, key: "booking", page: "booking" },
				{ href: `/hospital${suffix}#hc-contact`, key: "contact", page: "home" },
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
			const hospitalName = cfg[this.nameField()] || cfg.hospital_name_ar || "Hospital";
			const hero = document.getElementById("hc-home-hero");
			if (hero) {
				const heroImg =
					cfg.hero_image ||
					"https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80";
				const heroText = cfg[this.textField("hero_text")] || "";
				hero.className = "hc-hero hc-hero-split";
				hero.innerHTML = `
					<div class="hc-hero-visual"><img src="${this.esc(heroImg)}" alt="${this.esc(hospitalName)}" loading="eager"></div>
					<div class="hc-hero-copy">
						<h1>${this.esc(cfg[this.textField("tagline")] || "")}</h1>
						<p>${this.esc(heroText)}</p>
						<div class="hc-hero-actions">
							<a class="hc-btn hc-btn-primary" href="/hospital/booking${suffix}">${this.t("book_now_cta")}</a>
							<a class="hc-btn hc-btn-outline" href="#hc-contact">${this.t("contact_us")}</a>
						</div>
					</div>`;
			}

			const featuresBar = document.getElementById("hc-features-bar");
			if (featuresBar) {
				featuresBar.className = "hc-features-bar hc-features-pro";
				featuresBar.innerHTML = FEATURES.map(
					(f) =>
						`<div class="hc-feature-item"><div class="hc-feature-icon">${FEATURE_SVGS[f.key] || ""}</div>${this.lang === "ar" ? f.ar : f.en}</div>`
				).join("");
			}

			const deptTitle = document.getElementById("hc-dept-title");
			if (deptTitle && deptTitle.nextElementSibling) {
				deptTitle.nextElementSibling.textContent = this.t("dept_sub");
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
								(d) => `<a class="hc-card hc-dept-card hc-dept-pro" href="/hospital/clinic${this.querySuffix({ department: d.name })}">
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
				const rows = this.pickFeaturedServices(r.message || []);
				const servicesTitle = servicesWrap.previousElementSibling;
				if (servicesTitle) {
					const sub = servicesTitle.querySelector("p");
					if (sub) sub.textContent = this.t("featured_services_sub");
				}
				servicesWrap.innerHTML = rows.length
					? `<div class="hc-grid-4">${rows
							.map((s) => {
								const img = s.website_image || SERVICE_IMAGES[s.service_type] || SERVICE_IMAGES.default;
								return `<div class="hc-card hc-service-card hc-service-pro">
									<img class="hc-service-img" src="${this.esc(img)}" alt="">
									<div class="hc-card-body">
										<h3>${this.esc(s.service_title)}</h3>
										<p class="text-muted">${this.esc(s.website_description || "")}</p>
										<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix({ service: s.service_code })}">${this.t("book_now")}</a>
									</div>
								</div>`;
							})
							.join("")}</div>`
					: "";
			}
		},

		async init_doctors() {
			const sub = document.getElementById("hc-doctors-subtitle");
			if (sub) sub.textContent = this.t("doctors_sub");
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
							(d) => `<div class="hc-card hc-doctor-card hc-doctor-pro">
								<div class="hc-doctor-photo">${d.photo ? `<img src="${this.esc(d.photo)}" alt="">` : "👨‍⚕️"}</div>
								<div class="hc-doctor-body">
									<h3>${this.esc(d.practitioner_name)}</h3>
									<div>${this.esc(d.specialty_name || "")}</div>
									<div>${this.esc(String(d.years_of_experience || 5))} ${this.t("years_exp")}</div>
									<div class="hc-doctor-meta">
										<span class="hc-rating">★ ${this.esc(String(d.rating || "4.9"))}</span>
										<span>${this.lang === "ar" ? "ترخيص" : "License"}: ${this.esc(d.license_number || "—")}</span>
									</div>
									<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix({ practitioner: d.name })}">${this.t("book_now")}</a>
								</div>
							</div>`
						)
						.join("")}</div>
					<div style="text-align:center;margin-top:28px;">
						<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix()}">${this.t("view_all_doctors")}</a>
					</div>`;
				wrap.querySelectorAll(".hc-pill").forEach((btn) => {
					btn.addEventListener("click", () => {
						filter = btn.dataset.filter;
						render();
					});
				});
			};
			render();
		},

		async init_clinic() {
			const dept = this.params.get("department");
			const hero = document.getElementById("hc-clinic-hero");
			const wrap = document.getElementById("hc-clinic-page");
			if (!dept || !wrap) {
				if (wrap) wrap.innerHTML = `<div class="hc-empty">${this.lang === "ar" ? "اختر قسماً من الصفحة الرئيسية." : "Select a department from home."}</div>`;
				return;
			}
			const r = await frappe.call({
				method: "omnexa_healthcare.api.public_hospital_site.get_department_clinic",
				args: { ...this.siteArgs(), department: dept },
			});
			const d = r.message || {};
			const desc = this.lang === "ar" ? d.description_ar : d.description_en;
			const services = (this.lang === "ar" ? d.services_ar : d.services_en) || [];
			const hours = this.lang === "ar" ? d.working_hours_ar : d.working_hours_en;
			if (hero) {
				hero.innerHTML = `<div class="hc-wrap hc-clinic-hero-inner">
					<div>${d.image ? `<img src="${this.esc(d.image)}" alt="">` : `<div style="font-size:5rem;text-align:center">${d.icon || "🏥"}</div>`}</div>
					<div>
						<p class="text-muted">${this.lang === "ar" ? "الرئيسية / العيادات" : "Home / Clinics"} / ${this.esc(d.department_name)}</p>
						<h1 style="color:var(--hc-primary)">${this.esc(d.department_name)}</h1>
						<p>${this.esc(desc || "")}</p>
						<a class="hc-btn hc-btn-primary" href="/hospital/booking${this.querySuffix({ department: d.name })}">${this.t("book_clinic")}</a>
					</div>
				</div>`;
			}
			wrap.innerHTML = `
				<div class="hc-clinic-panel">
					<h3>${this.t("working_hours")}</h3>
					<p>${this.esc(hours || (this.lang === "ar" ? "حسب جدول المستشفى" : "Per hospital schedule"))}</p>
				</div>
				<div class="hc-clinic-panel">
					<h3>${this.t("services_offered")}</h3>
					<ul class="hc-clinic-services">${services.map((s) => `<li>${this.esc(s)}</li>`).join("") || `<li>—</li>`}</ul>
				</div>`;
		},

		async init_booking() {
			const title = document.getElementById("hc-booking-title");
			if (title) title.textContent = this.t("booking");
			const sub = document.getElementById("hc-booking-subtitle");
			if (sub) sub.textContent = this.t("booking_sub");
			document.title = `${this.t("booking")} | ${this.t("booking")}`;
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
				patientId: "",
				sessionToken: "",
			};
			let doctors = [];

			const [deptsR, doctorsR, servicesR] = await Promise.all([
				frappe.call({ method: "omnexa_healthcare.api.public_hospital_site.get_published_departments", args: this.siteArgs() }),
				frappe.call({ method: "omnexa_healthcare.api.public_hospital_site.get_published_doctors", args: this.siteArgs() }),
				frappe.call({ method: "omnexa_healthcare.api.web_booking.get_published_services", args: { company: cfg.company, branch: cfg.branch } }),
			]);
			const departments = deptsR.message || [];
			doctors = doctorsR.message || [];
			const services = servicesR.message || [];

			const steps = [
				this.t("step_department"),
				this.t("step_doctor"),
				this.t("step_time"),
				this.t("step_personal"),
				this.t("otp") || "OTP",
				this.t("step_confirm"),
			];

			const loadDoctors = async () => {
				const args = { ...this.siteArgs() };
				if (state.department) args.department = state.department;
				let r = await frappe.call({
					method: "omnexa_healthcare.api.public_hospital_site.get_published_doctors",
					args,
				});
				doctors = r.message || [];
				if (state.department && !doctors.length) {
					r = await frappe.call({
						method: "omnexa_healthcare.api.public_hospital_site.get_published_doctors",
						args: this.siteArgs(),
					});
					doctors = r.message || [];
				}
			};

			const syncPatientFromForm = () => {
				const given = document.getElementById("hc-given");
				const family = document.getElementById("hc-family");
				const phone = document.getElementById("hc-phone");
				const email = document.getElementById("hc-email");
				const nid = document.getElementById("hc-nid");
				const birth = document.getElementById("hc-birth");
				const gender = document.getElementById("hc-gender");
				if (!given) return false;
				state.patient = {
					given_name: given.value.trim(),
					family_name: family.value.trim(),
					phone: phone.value.trim(),
					email: email.value.trim(),
					national_id: nid ? nid.value.trim() : "",
					birth_date: birth ? birth.value : "",
					gender: gender ? gender.value : "",
					company: cfg.company,
					branch: cfg.branch,
				};
				return !!(
					state.patient.given_name &&
					state.patient.family_name &&
					state.patient.phone &&
					state.patient.email &&
					state.patient.national_id &&
					state.patient.birth_date &&
					state.patient.gender
				);
			};

			const advance = () => {
				state.step += 1;
				render();
			};

			const render = async () => {
				shell.innerHTML = `
					<div class="hc-steps hc-steps-ring">${steps
						.map(
							(label, idx) =>
								`<div class="hc-step-ring ${state.step === idx + 1 ? "active" : ""} ${state.step > idx + 1 ? "done" : ""}">
									<div class="num">${idx + 1}</div><span>${label}</span>
								</div>`
						)
						.join("")}</div>
					<div class="hc-panel" id="hc-booking-panel"></div>
					<div style="display:flex;justify-content:space-between;margin-top:16px;">
						<button type="button" class="hc-btn hc-btn-outline" id="hc-book-back" ${state.step === 1 ? "disabled" : ""}>${this.t("back")}</button>
						${state.step === 6 ? `<button type="button" class="hc-btn hc-btn-primary" id="hc-book-next">${this.t("confirm")}</button>` : ""}
					</div>`;

				const panel = document.getElementById("hc-booking-panel");
				if (state.step === 1) {
					panel.innerHTML = `<h3 style="margin-top:0;color:var(--hc-primary)">${this.t("choose_department")}</h3>
					<div class="hc-grid-4">${departments
						.map(
							(d) =>
								`<button type="button" class="hc-card hc-dept-card hc-dept-pro ${state.department === d.name ? "selected" : ""}" data-dept="${this.esc(d.name)}">
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
							state.slot = null;
							state.step = 2;
							render();
						});
					});
				} else if (state.step === 2) {
					await loadDoctors();
					panel.innerHTML = doctors.length
						? `<div class="hc-grid-3">${doctors
								.map(
									(d) => `<button type="button" class="hc-card hc-doctor-card ${state.practitioner === d.name ? "selected" : ""}" data-doc="${this.esc(d.name)}">
								<div class="hc-doctor-photo" style="height:140px;">${d.photo ? `<img src="${this.esc(d.photo)}">` : "👨‍⚕️"}</div>
								<strong>${this.esc(d.practitioner_name)}</strong>
								<div>${this.esc(d.specialty_name || "")}</div>
							</button>`
								)
								.join("")}</div>`
						: `<div class="hc-empty">${this.t("no_doctors")}</div>`;
					panel.querySelectorAll("[data-doc]").forEach((btn) => {
						btn.addEventListener("click", () => {
							state.practitioner = btn.dataset.doc;
							const doc = doctors.find((x) => x.name === state.practitioner);
							state.service_code =
								(doc && doc.service_codes && doc.service_codes[0]) ||
								(services.find((s) => s.default_practitioner === state.practitioner) || {}).service_code ||
								(services.find((s) => s.department === state.department) || {}).service_code ||
								state.service_code;
							state.slot = null;
							state.step = 3;
							render();
						});
					});
				} else if (state.step === 3) {
					panel.innerHTML = `
						<div class="hc-field" style="max-width:280px;margin-bottom:16px;">
							<label>${this.t("date")}</label>
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
											`<button type="button" class="hc-slot ${state.slot && state.slot.start === s.start ? "selected" : ""}" data-start="${this.esc(s.start)}" data-end="${this.esc(s.end)}">${this.esc(String(s.start).slice(11, 16))}</button>`
									)
									.join("")
							: `<div class="hc-empty">${this.t("no_slots")}</div>`;
						slotsEl.querySelectorAll(".hc-slot").forEach((btn) => {
							btn.addEventListener("click", () => {
								state.slot = { start: btn.dataset.start, end: btn.dataset.end };
								state.step = 4;
								render();
							});
						});
					};
					document.getElementById("hc-book-date").addEventListener("change", loadSlots);
					await loadSlots();
				} else if (state.step === 4) {
					panel.innerHTML = `
						<p class="hc-muted" style="margin-top:0">${this.t("registration_required") || "Full registration required before booking"}</p>
						<div class="hc-form-grid">
							<div class="hc-field"><label>${this.t("first_name")}</label><input id="hc-given" value="${this.esc(state.patient.given_name || "")}"></div>
							<div class="hc-field"><label>${this.t("last_name")}</label><input id="hc-family" value="${this.esc(state.patient.family_name || "")}"></div>
							<div class="hc-field"><label>${this.t("national_id") || "National ID"}</label><input id="hc-nid" value="${this.esc(state.patient.national_id || "")}"></div>
							<div class="hc-field"><label>${this.t("phone")}</label><input id="hc-phone" value="${this.esc(state.patient.phone || "")}"></div>
							<div class="hc-field"><label>${this.t("email")}</label><input id="hc-email" type="email" value="${this.esc(state.patient.email || "")}"></div>
							<div class="hc-field"><label>${this.t("birth_date") || "Birth date"}</label><input id="hc-birth" type="date" value="${this.esc(state.patient.birth_date || "")}"></div>
							<div class="hc-field"><label>${this.t("gender") || "Gender"}</label>
								<select id="hc-gender"><option value="">${this.t("select") || "Select"}</option>
								<option value="male">${this.t("male") || "Male"}</option><option value="female">${this.t("female") || "Female"}</option></select></div>
						</div>
						<button type="button" class="hc-btn hc-btn-primary" id="hc-reg-next" style="margin-top:12px">${this.t("register_send_otp") || "Register & Send OTP"}</button>`;
					document.getElementById("hc-reg-next")?.addEventListener("click", async () => {
						if (!syncPatientFromForm()) {
							frappe.msgprint(this.t("fill_all_fields") || "Please fill all required fields");
							return;
						}
						try {
							const r = await frappe.call({
								method: "omnexa_healthcare.api.web_booking.register_for_booking",
								args: { payload: state.patient },
							});
							state.patientId = (r.message && r.message.patient) || "";
							if (r.message && r.message.demo_otp) frappe.show_alert({ message: `OTP: ${r.message.demo_otp}`, indicator: "blue" });
							state.step = 5;
							render();
						} catch (e) {
							frappe.msgprint((e && e.message) || "Registration failed");
						}
					});
				} else if (state.step === 5) {
					panel.innerHTML = `
						<h3>${this.t("otp") || "OTP Verification"}</h3>
						<div class="hc-field" style="max-width:240px"><label>${this.t("otp_code") || "OTP Code"}</label><input id="hc-otp" maxlength="6"></div>
						<button type="button" class="hc-btn hc-btn-primary" id="hc-otp-verify">${this.t("verify") || "Verify"}</button>`;
					document.getElementById("hc-otp-verify")?.addEventListener("click", async () => {
						const otp = document.getElementById("hc-otp").value;
						try {
							const r = await frappe.call({
								method: "omnexa_healthcare.api.web_booking.verify_for_booking",
								args: { mobile: state.patient.phone, otp, patient: state.patientId },
							});
							state.sessionToken = (r.message && r.message.session_token) || "";
							state.step = 6;
							render();
						} catch (e) {
							frappe.msgprint((e && e.message) || "OTP failed");
						}
					});
				} else if (state.step === 6) {
					const doc = doctors.find((d) => d.name === state.practitioner);
					panel.innerHTML = `
						<h3>${this.t("booking_summary")}</h3>
						<ul style="line-height:2;">
							<li><b>${this.t("doctor")}:</b> ${this.esc((doc && doc.practitioner_name) || state.practitioner)}</li>
							<li><b>${this.t("slot")}:</b> ${this.esc(state.slot ? `${state.slot.start} — ${state.slot.end}` : "")}</li>
							<li><b>${this.t("patient")}:</b> ${this.esc(`${state.patient.given_name || ""} ${state.patient.family_name || ""}`.trim())}</li>
							<li><b>${this.t("phone")}:</b> ${this.esc(state.patient.phone || "")}</li>
						</ul>
						<div id="hc-book-result"></div>`;
				}

				document.getElementById("hc-book-back")?.addEventListener("click", () => {
					if (state.step > 1) {
						state.step -= 1;
						render();
					}
				});
				document.getElementById("hc-book-next")?.addEventListener("click", async () => {
					if (state.step === 6) {
						await this.submitBooking(state, cfg);
					}
				});
			};

			if (!state.service_code && state.practitioner) {
				const doc = doctors.find((d) => d.name === state.practitioner);
				state.service_code = (doc && doc.service_codes && doc.service_codes[0]) || "";
			}
			if (state.practitioner && state.service_code) {
				state.step = 3;
			} else if (state.department) {
				state.step = 2;
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
				frappe.msgprint(this.t("no_service"));
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
							patient: state.patientId,
							session_token: state.sessionToken,
							appointment_date: state.slot.start,
							slot_end: state.slot.end,
						},
					},
				});
				const msg = r.message || {};
				const el = document.getElementById("hc-book-result");
				if (el) {
					el.innerHTML = `<div class="alert alert-success">${this.t("booking_success")}: <b>${this.esc(msg.name)}</b></div>`;
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
