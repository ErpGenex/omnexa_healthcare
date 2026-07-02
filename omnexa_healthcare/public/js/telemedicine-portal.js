/* global frappe */
(function () {
  const STORAGE_LANG = "hc_telemedicine_lang";
  const SPECIALTIES = [
    { key: "general", ar: "طب عام", en: "General Practice", icon: "🏥" },
    { key: "cardiology", ar: "أمراض القلب", en: "Cardiology", icon: "❤️" },
    { key: "dermatology", ar: "جلدية", en: "Dermatology", icon: "🔬" },
    { key: "pediatrics", ar: "أطفال", en: "Pediatrics", icon: "👶" },
    { key: "gynecology", ar: "نساء وتوليد", en: "Gynecology", icon: "👩" },
    { key: "orthopedics", ar: "عظام", en: "Orthopedics", icon: "🦴" },
    { key: "neurology", ar: "أعصاب", en: "Neurology", icon: "🧠" },
    { key: "psychiatry", ar: "طب نفسي", en: "Psychiatry", icon: "🧘" },
    { key: "ophthalmology", ar: "عيون", en: "Ophthalmology", icon: "👁️" },
    { key: "ent", ar: "أنف وأذن وحنجرة", en: "ENT", icon: "👂" },
    { key: "gastroenterology", ar: "جهاز هضمي", en: "Gastroenterology", icon: "🫁" },
    { key: "endocrinology", ar: "غدد صماء", en: "Endocrinology", icon: "💉" },
  ];

  const FEATURES = [
    { key: "video", ar: "استشارة فيديو", en: "Video Consultation", icon: "📹" },
    { key: "voice", ar: "استشارة صوتية", en: "Voice Consultation", icon: "📞" },
    { key: "chat", ar: "محادثة", en: "Chat Consultation", icon: "💬" },
    { key: "secure", ar: "آمن ومشفر", en: "Secure & Encrypted", icon: "🔒" },
    { key: "records", ar: "سجلات طبية", en: "Medical Records", icon: "📋" },
    { key: "prescription", ar: "وصفات إلكترونية", en: "E-Prescriptions", icon: "💊" },
  ];

  const BENEFITS = [
    { key: "home", ar: "من منزلك", en: "From Home", icon: "🏠" },
    { key: "time", ar: "وفر الوقت", en: "Save Time", icon: "⏰" },
    { key: "safe", ar: "آمن وخاص", en: "Safe & Private", icon: "🔒" },
    { key: "cost", ar: "تكلفة أقل", en: "Lower Cost", icon: "💰" },
    { key: "easy", ar: "سهل الاستخدام", en: "Easy to Use", icon: "📱" },
    { key: "doctors", ar: "أطباء مختصون", en: "Specialist Doctors", icon: "👨‍⚕️" },
  ];

  window.TelemedicinePortal = {
    lang: localStorage.getItem(STORAGE_LANG) || "ar",
    page: null,
    config: null,
    bookingData: {},
    currentStep: 1,

    apiResult(response) {
      return response.message || {};
    },

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
        telemedicine: { ar: "الطب عن بعد", en: "Telemedicine" },
        book: { ar: "احجز استشارة", en: "Book Consultation" },
        doctors: { ar: "الأطباء", en: "Doctors" },
        specialties: { ar: "التخصصات", en: "Specialties" },
        benefits: { ar: "المميزات", en: "Benefits" },
        book_now: { ar: "احجز الآن", en: "Book Now" },
        learn_more: { ar: "اعرف المزيد", en: "Learn More" },
        how_it_works: { ar: "كيف يعمل؟", en: "How It Works" },
        choose_specialty: { ar: "اختر التخصص", en: "Choose Specialty" },
        choose_doctor: { ar: "اختر الطبيب", en: "Choose Doctor" },
        choose_time: { ar: "اختر الموعد", en: "Choose Time" },
        choose_type: { ar: "نوع الاستشارة", en: "Consultation Type" },
        confirm: { ar: "تأكيد", en: "Confirm" },
        video: { ar: "فيديو", en: "Video" },
        voice: { ar: "صوت", en: "Voice" },
        chat: { ar: "محادثة", en: "Chat" },
        back: { ar: "السابق", en: "Back" },
        next: { ar: "التالي", en: "Next" },
        submit: { ar: "إرسال", en: "Submit" },
        loading: { ar: "جاري التحميل...", en: "Loading..." },
        no_slots: { ar: "لا توجد مواعيد متاحة", en: "No slots available" },
        no_doctors: { ar: "لا يوجد أطباء متاحون", en: "No doctors available" },
        session_title: { ar: "استشارة طبية", en: "Medical Consultation" },
        chat: { ar: "المحادثة", en: "Chat" },
        records: { ar: "السجلات", en: "Records" },
        end_call: { ar: "إنهاء", en: "End Call" },
        mic: { ar: "ميكروفون", en: "Microphone" },
        camera: { ar: "كاميرا", en: "Camera" },
        screen: { ar: "مشاركة الشاشة", en: "Share Screen" },
        whiteboard: { ar: "سبورة", en: "Whiteboard" },
        file: { ar: "ملف", en: "File" },
        settings: { ar: "إعدادات", en: "Settings" },
        connecting: { ar: "جاري الاتصال...", en: "Connecting..." },
        connected: { ar: "متصل", en: "Connected" },
        disconnected: { ar: "منقطع", en: "Disconnected" },
        recording: { ar: "جاري التسجيل", en: "Recording" },
        vitals: { ar: "القياسات الحيوية", en: "Vitals" },
        medications: { ar: "الأدوية", en: "Medications" },
        allergies: { ar: "الحساسية", en: "Allergies" },
        conditions: { ar: "الأمراض المزمنة", en: "Chronic Conditions" },
        rating: { ar: "قيّم الاستشارة", en: "Rate Consultation" },
        feedback: { ar: "ملاحظاتك", en: "Your Feedback" },
        confirm_end: { ar: "هل أنت متأكد من إنهاء الاستشارة؟", en: "Are you sure you want to end the consultation?" },
      };
      return (map[key] && map[key][this.lang]) || key;
    },

    async loadConfig() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_portal_config",
        });
        this.config = r.message?.config || {};
      } catch (e) {
        console.error("Failed to load config:", e);
        this.config = {
          enable_video: true,
          enable_voice: true,
          enable_chat: true,
          default_duration: 30,
          max_duration: 60,
          enable_screen_sharing: true,
          enable_whiteboard: true,
          enable_file_sharing: true,
          video_quality: "HD",
          primary_color: "#0066cc",
          secondary_color: "#004499"
        };
      }
    },

    applyTheme() {
      const site = document.querySelector(".hc-telemedicine");
      if (!site) return;
      
      if (this.config.primary_color) {
        site.style.setProperty("--hc-tele-primary", this.config.primary_color);
      }
      if (this.config.secondary_color) {
        site.style.setProperty("--hc-tele-secondary", this.config.secondary_color);
      }
      
      site.dir = this.lang === "ar" ? "rtl" : "ltr";
    },

    renderChrome() {
      this.renderHeader();
      this.renderFeatures();
      this.renderStats();
      this.renderFooter();
    },

    renderHeader() {
      const header = document.getElementById("hc-header");
      if (!header) return;

      const nav = [
        { key: "home", href: "/telemedicine" },
        { key: "book", href: "/telemedicine/book" },
        { key: "doctors", href: "/telemedicine/doctors" },
      ];

      header.innerHTML = `
        <div class="hc-wrap">
          <div class="hc-header-inner">
            <div class="hc-brand">
              <span>${this.t("telemedicine")}</span>
            </div>
            <nav class="hc-nav">
              ${nav.map(item => `
                <a href="${item.href}" class="${this.page === item.key ? 'active' : ''}">
                  ${this.t(item.key)}
                </a>
              `).join('')}
            </nav>
            <div class="hc-actions">
              <button class="hc-lang" onclick="TelemedicinePortal.toggleLang()">
                ${this.lang === "ar" ? "EN" : "عربي"}
              </button>
              <a class="hc-btn hc-btn-primary" href="/telemedicine/book">
                ${this.t("book_now")}
              </a>
            </div>
            <button class="hc-mobile-toggle" onclick="TelemedicinePortal.toggleMobileNav()">
              ☰
            </button>
          </div>
        </div>
      `;
    },

    renderFeatures() {
      const featuresBar = document.getElementById("hc-features-bar");
      if (!featuresBar) return;

      featuresBar.innerHTML = FEATURES.map(f => `
        <div class="hc-feature-item">
          <span>${f.icon}</span>
          ${this.t(f.key)}
        </div>
      `).join('');
    },

    renderStats() {
      const stats = document.getElementById("hc-stats");
      if (!stats) return;

      stats.innerHTML = `
        <div class="hc-wrap">
          <div class="hc-stats-grid">
            <div class="hc-stat-item">
              <div class="hc-stat-num">10,000+</div>
              <div class="hc-stat-label">${this.t("doctors")}</div>
            </div>
            <div class="hc-stat-item">
              <div class="hc-stat-num">50,000+</div>
              <div class="hc-stat-label">Consultations</div>
            </div>
            <div class="hc-stat-item">
              <div class="hc-stat-num">4.8/5</div>
              <div class="hc-stat-label">Rating</div>
            </div>
            <div class="hc-stat-item">
              <div class="hc-stat-num">24/7</div>
              <div class="hc-stat-label">Available</div>
            </div>
          </div>
        </div>
      `;
    },

    renderFooter() {
      const footer = document.getElementById("hc-footer");
      if (!footer) return;

      footer.innerHTML = `
        <div class="hc-wrap">
          <div class="hc-footer-grid">
            <div>
              <h4>${this.t("telemedicine")}</h4>
              <p>World-class telemedicine platform</p>
            </div>
            <div>
              <h4>Links</h4>
              <a href="/telemedicine">${this.t("home")}</a>
              <a href="/telemedicine/book">${this.t("book")}</a>
              <a href="/telemedicine/doctors">${this.t("doctors")}</a>
            </div>
            <div>
              <h4>Contact</h4>
              <p>support@telemedicine.com</p>
              <p>+966 12 345 6789</p>
            </div>
          </div>
          <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
            <p>© 2026 Telemedicine Portal. All rights reserved.</p>
          </div>
        </div>
      `;
    },

    toggleLang() {
      this.lang = this.lang === "ar" ? "en" : "ar";
      localStorage.setItem(STORAGE_LANG, this.lang);
      location.reload();
    },

    toggleMobileNav() {
      const nav = document.querySelector(".hc-nav");
      nav.classList.toggle("open");
    },

    // Home Page
    init_home() {
      this.renderSpecialties();
      this.renderBenefits();
      this.loadFeaturedDoctors();
    },

    renderSpecialties() {
      const grid = document.getElementById("hc-specialties-grid");
      if (!grid) return;

      grid.innerHTML = SPECIALTIES.map(s => `
        <div class="hc-card hc-dept-card" onclick="TelemedicinePortal.selectSpecialty('${s.key}')">
          <div class="hc-dept-icon">${s.icon}</div>
          <h4>${s.ar}</h4>
          <p class="text-muted">${s.en}</p>
        </div>
      `).join('');
    },

    renderBenefits() {
      const grid = document.getElementById("hc-benefits-grid");
      if (!grid) return;

      grid.innerHTML = BENEFITS.map(b => `
        <div class="hc-card hc-benefit-card">
          <div class="hc-benefit-icon">${b.icon}</div>
          <h4>${b.ar}</h4>
          <p class="text-muted">${b.en}</p>
        </div>
      `).join('');
    },

    async loadFeaturedDoctors() {
      const grid = document.getElementById("hc-doctors-grid");
      if (!grid) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_available_doctors",
        });
        const result = this.apiResult(r);
        const doctors = (result.doctors || []).slice(0, 8);
        if (!doctors.length) {
          grid.innerHTML = `<div class="hc-empty"><p>${this.t("no_doctors")}</p></div>`;
          return;
        }

        grid.innerHTML = doctors.map(d => `
          <div class="hc-card hc-doctor-card">
            <div class="hc-doctor-photo"><span>👨‍⚕️</span></div>
            <div class="hc-doctor-body">
              <h4>${d.practitioner_name}</h4>
              <p class="text-muted">${d.specialty || this.t("doctors")}</p>
              <div class="hc-doctor-meta">
                <span>⭐ ${d.average_rating || "4.8"}</span>
                <span>${d.session_count || 0} ${this.lang === "ar" ? "جلسة" : "sessions"}</span>
              </div>
            </div>
            <button class="hc-btn hc-btn-primary" onclick="TelemedicinePortal.bookDoctor('${d.name}')">
              ${this.t("book_now")}
            </button>
          </div>
        `).join("");
      } catch (e) {
        console.error("Failed to load doctors:", e);
      }
    },

    renderDoctors() {
      this.loadFeaturedDoctors();
    },

    selectSpecialty(key) {
      this.bookingData.specialty = key;
      window.location.href = `/telemedicine/book?specialty=${key}`;
    },

    bookDoctor(practitionerId) {
      this.bookingData.doctor = practitionerId;
      this.bookingData.practitioner = practitionerId;
      window.location.href = `/telemedicine/book?doctor=${encodeURIComponent(practitionerId)}`;
    },

    // Booking Page
    init_booking() {
      this.doctorFilter = "all";
      this.bookingData.consultation_type = this.bookingData.consultation_type || "video";
      this.initBookingSteps();
      this.initConsultationTypes();
      this.initDoctorFilters();
      this.loadSpecialties();

      if (this.bookingData.specialty) {
        this.currentStep = 2;
      }
      if (this.bookingData.doctor || this.bookingData.practitioner) {
        this.bookingData.practitioner = this.bookingData.practitioner || this.bookingData.doctor;
        this.currentStep = 3;
      }

      this.updateStepUI();
      this.onEnterStep(this.currentStep);
    },

    initConsultationTypes() {
      const cards = document.querySelectorAll("#hc-consultation-types .hc-consultation-type");
      cards.forEach((card) => {
        card.onclick = () => this.selectConsultationType(card.dataset.type);
      });
      this.selectConsultationType(this.bookingData.consultation_type || "video", false);
    },

    selectConsultationType(type, autoAdvance = true) {
      this.bookingData.consultation_type = type;
      document.querySelectorAll("#hc-consultation-types .hc-consultation-type").forEach((card) => {
        card.classList.toggle("selected", card.dataset.type === type);
      });
      if (autoAdvance && this.currentStep === 4) {
        setTimeout(() => this.nextStep(), 250);
      }
    },

    initDoctorFilters() {
      document.querySelectorAll("#hc-doctor-filters .hc-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
          document.querySelectorAll("#hc-doctor-filters .hc-pill").forEach((p) => p.classList.remove("active"));
          pill.classList.add("active");
          this.doctorFilter = pill.dataset.filter || "all";
          this.loadDoctors();
        });
      });
    },

    validateCurrentStep() {
      const msg = (ar, en) => alert(this.lang === "ar" ? ar : en);
      switch (this.currentStep) {
        case 1:
          if (!this.bookingData.specialty) {
            msg("يرجى اختيار التخصص", "Please select a specialty");
            return false;
          }
          return true;
        case 2:
          if (!this.bookingData.practitioner && !this.bookingData.doctor) {
            msg("يرجى اختيار الطبيب", "Please select a doctor");
            return false;
          }
          return true;
        case 3:
          if (!this.bookingData.time?.start) {
            msg("يرجى اختيار موعد", "Please select a time slot");
            return false;
          }
          return true;
        case 4:
          if (!this.bookingData.consultation_type) {
            msg("يرجى اختيار نوع الاستشارة", "Please select consultation type");
            return false;
          }
          return true;
        default:
          return true;
      }
    },

    onEnterStep(step) {
      if (step === 2) this.loadDoctors();
      if (step === 3) {
        this.initDatepicker();
        this.loadSlots();
      }
      if (step === 4) this.initConsultationTypes();
      if (step === 5) {
        this.loadBookingPatients();
        this.updateBookingSummary();
      }
    },

    updateBookingSummary() {
      const doctorLabel = document.getElementById("hc-summary-doctor");
      const specialtyLabel = document.getElementById("hc-summary-specialty");
      const dateLabel = document.getElementById("hc-summary-date");
      const timeLabel = document.getElementById("hc-summary-time");
      const typeLabel = document.getElementById("hc-summary-type");
      const typeMap = { video: this.t("video"), voice: this.t("voice"), chat: this.t("chat") };
      const specialty = SPECIALTIES.find((s) => s.key === this.bookingData.specialty);

      if (doctorLabel) doctorLabel.textContent = this.bookingData.doctor_name || this.bookingData.practitioner || "-";
      if (specialtyLabel) specialtyLabel.textContent = specialty ? specialty.ar : (this.bookingData.specialty || "-");
      if (dateLabel) dateLabel.textContent = document.getElementById("hc-booking-date")?.value || "-";
      if (timeLabel) timeLabel.textContent = this.bookingData.time?.start || "-";
      if (typeLabel) typeLabel.textContent = typeMap[this.bookingData.consultation_type] || "-";
    },

    async loadBookingPatients() {
      const select = document.getElementById("hc-booking-patient");
      if (!select) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_booking_patients",
        });
        const result = this.apiResult(r);
        const patients = result.patients || [];
        select.innerHTML = `<option value="">${this.lang === "ar" ? "اختر المريض" : "Select patient"}</option>` +
          patients.map(p => `<option value="${p.name}">${p.full_name || p.name}</option>`).join("");
        if (patients.length) {
          this.bookingData.patient = patients[0].name;
          select.value = patients[0].name;
        }
        select.onchange = (e) => {
          this.bookingData.patient = e.target.value;
        };
      } catch (e) {
        console.error("Failed to load booking patients:", e);
      }
    },

    initBookingSteps() {
      const params = new URLSearchParams(window.location.search);
      if (params.get("specialty")) {
        this.bookingData.specialty = params.get("specialty");
      }
      if (params.get("doctor")) {
        this.bookingData.doctor = params.get("doctor");
      }

      this.updateStepUI();
      this.initBookingNavigation();
    },

    initBookingNavigation() {
      const nextBtn = document.getElementById("hc-next-btn");
      const backBtn = document.getElementById("hc-back-btn");

      if (nextBtn) {
        nextBtn.addEventListener("click", () => this.nextStep());
      }
      if (backBtn) {
        backBtn.addEventListener("click", () => this.prevStep());
      }
    },

    updateStepUI() {
      for (let i = 1; i <= 5; i++) {
        const step = document.querySelector(`.hc-step-ring[data-step="${i}"]`);
        const content = document.querySelector(`.hc-booking-step[data-step="${i}"]`);
        
        if (step) {
          step.classList.remove("active", "done");
          if (i < this.currentStep) step.classList.add("done");
          if (i === this.currentStep) step.classList.add("active");
        }
        
        if (content) {
          content.style.display = i === this.currentStep ? "block" : "none";
        }
      }

      const backBtn = document.getElementById("hc-back-btn");
      const nextBtn = document.getElementById("hc-next-btn");
      
      if (backBtn) {
        backBtn.style.display = this.currentStep > 1 ? "inline-block" : "none";
        backBtn.querySelector("span").textContent = this.t("back");
      }
      
      if (nextBtn) {
        nextBtn.querySelector("span").textContent = this.currentStep === 5 ? this.t("submit") : this.t("next");
      }
    },

    nextStep() {
      if (!this.validateCurrentStep()) return;
      if (this.currentStep < 5) {
        this.currentStep++;
        this.onEnterStep(this.currentStep);
        this.updateStepUI();
      } else {
        this.submitBooking();
      }
    },

    prevStep() {
      if (this.currentStep > 1) {
        this.currentStep--;
        this.updateStepUI();
      }
    },

    loadSpecialties() {
      const list = document.getElementById("hc-specialties-list");
      if (!list) return;

      list.innerHTML = SPECIALTIES.map(s => `
        <div class="hc-card hc-consultation-type ${this.bookingData.specialty === s.key ? 'selected' : ''}" 
             onclick="TelemedicinePortal.selectBookingSpecialty('${s.key}')">
          <div class="hc-type-icon">${s.icon}</div>
          <h4>${s.ar}</h4>
          <p class="text-muted">${s.en}</p>
        </div>
      `).join('');
    },

    selectBookingSpecialty(key) {
      this.bookingData.specialty = key;
      this.loadSpecialties();
      // Auto-advance to next step
      setTimeout(() => this.nextStep(), 300);
    },

    async loadDoctors() {
      const list = document.getElementById("hc-doctors-list");
      const empty = document.getElementById("hc-no-doctors");
      if (!list) return;

      list.innerHTML = `<div class="hc-empty"><p>${this.t("loading")}</p></div>`;
      if (empty) empty.style.display = "none";

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_available_doctors",
          args: { specialty: this.bookingData.specialty },
        });
        const result = this.apiResult(r);
        let doctors = result.doctors || [];

        if (this.doctorFilter === "top-rated") {
          doctors = [...doctors].sort((a, b) => (b.average_rating || 0) - (a.average_rating || 0));
        }

        if (!doctors.length) {
          list.innerHTML = "";
          if (empty) empty.style.display = "block";
          return;
        }

        if (empty) empty.style.display = "none";
        const fallbackNote = result.specialty_fallback
          ? `<p class="text-muted">${this.lang === "ar" ? "عرض جميع الأطباء المتاحين لهذا التخصص" : "Showing all available doctors"}</p>`
          : "";

        list.innerHTML = fallbackNote + doctors.map((d) => `
          <div class="hc-card hc-doctor-card" onclick="TelemedicinePortal.selectBookingDoctor('${d.name}', '${(d.practitioner_name || "").replace(/'/g, "\\'")}')">
            <div class="hc-doctor-photo"><span>👨‍⚕️</span></div>
            <div class="hc-doctor-body">
              <h4>${d.practitioner_name}</h4>
              <p class="text-muted">${d.specialty || this.t("doctors")}</p>
              <div class="hc-doctor-meta">
                <span>⭐ ${d.average_rating || "4.8"}</span>
                <span class="text-success">${this.lang === "ar" ? "متاح" : "Available"}</span>
              </div>
            </div>
          </div>
        `).join("");
      } catch (e) {
        console.error("Failed to load doctors:", e);
        list.innerHTML = `<div class="hc-empty"><p>${this.t("no_doctors")}</p></div>`;
      }
    },

    selectBookingDoctor(name, displayName) {
      this.bookingData.doctor = name;
      this.bookingData.practitioner = name;
      this.bookingData.doctor_name = displayName || name;
      setTimeout(() => this.nextStep(), 300);
    },

    initDatepicker() {
      const dateInput = document.getElementById("hc-booking-date");
      if (!dateInput) return;

      const today = new Date().toISOString().split("T")[0];
      dateInput.min = today;
      if (!dateInput.value) dateInput.value = today;

      dateInput.onchange = () => this.loadSlots();
      this.loadSlots();
    },

    async loadSlots() {
      const grid = document.getElementById("hc-slots-grid");
      const timeSelect = document.getElementById("hc-booking-time");
      const dateInput = document.getElementById("hc-booking-date");
      if (!grid) return;

      const date = dateInput?.value;
      const practitioner = this.bookingData.practitioner || this.bookingData.doctor;
      if (!date || !practitioner) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_available_slots",
          args: { practitioner_id: practitioner, date },
        });
        const result = this.apiResult(r);
        const slots = result.slots || [];

        grid.innerHTML = slots.length
          ? slots.map((s) => `
          <div class="hc-slot ${s.available ? "" : "disabled"} ${this.bookingData.time?.start === s.start ? "selected" : ""}"
               onclick="${s.available ? `TelemedicinePortal.selectSlot('${s.start}', '${s.end}')` : ""}">
            ${s.start} - ${s.end}
          </div>
        `).join("")
          : `<div class="hc-empty"><p>${this.lang === "ar" ? "لا توجد مواعيد" : "No slots available"}</p></div>`;

        if (timeSelect) {
          timeSelect.innerHTML = slots.filter(s => s.available).map(s =>
            `<option value="${s.start}|${s.end}">${s.start} - ${s.end}</option>`
          ).join("");
        }
      } catch (e) {
        console.error("Failed to load slots:", e);
      }
    },

    selectSlot(start, end) {
      this.bookingData.time = { start, end };
      // Auto-advance to next step
      setTimeout(() => this.nextStep(), 300);
    },

    async submitBooking() {
      const dateInput = document.getElementById("hc-booking-date");
      const patientSelect = document.getElementById("hc-booking-patient");
      const consent = document.getElementById("hc-consent");

      const patient = patientSelect?.value || this.bookingData.patient;
      if (!patient) {
        alert(this.lang === "ar" ? "يرجى اختيار المريض" : "Please select a patient");
        return;
      }
      if (consent && !consent.checked) {
        alert(this.lang === "ar" ? "يرجى الموافقة على الشروط" : "Please accept the terms");
        return;
      }

      const sessionTypeMap = { video: "Video", voice: "Voice", chat: "Chat" };
      const notes = [
        document.getElementById("hc-complaint")?.value,
        document.getElementById("hc-notes")?.value,
      ].filter(Boolean).join("\n");

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.book_telemedicine_consultation",
          args: {
            data: {
              patient,
              practitioner: this.bookingData.practitioner || this.bookingData.doctor,
              date: dateInput?.value,
              time: this.bookingData.time?.start,
              session_type: sessionTypeMap[this.bookingData.consultation_type] || "Video",
              notes,
            },
          },
        });
        const result = this.apiResult(r);
        if (result.success) {
          alert(this.lang === "ar" ? "تم الحجز بنجاح!" : "Booking confirmed!");
          window.location.href = `/telemedicine/session?session_id=${result.session_id}`;
        } else {
          alert(result.error || "Booking failed");
        }
      } catch (e) {
        console.error("Booking failed:", e);
        alert("Booking failed");
      }
    },

    // Session Page
    init_session() {
      this.sessionId = this.getSessionIdFromUrl();
      this.isDoctor = false;
      this.sessionPrescriptions = [];
      this.initSessionContext().then(() => {
        this.initRealtime();
        this.initVideoCall();
        this.loadChatHistory();
        this.initChat();
        this.initControls();
        this.initModals();
        this.loadPatientRecords();
        if (this.isDoctor) this.initDoctorTools();
      });
    },

    async initSessionContext() {
      if (!this.sessionId) return;
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_telemedicine_session",
          args: { session_id: this.sessionId },
        });
        const result = this.apiResult(r);
        if (!result.success || !result.session) return;

        this.isDoctor = !!result.session.is_practitioner;
        this.sessionPrescriptions = result.session.prescriptions || [];
        this.sessionData = result.session;

        const doctorName = document.getElementById("hc-doctor-name");
        const sessionTitle = document.getElementById("hc-session-title");
        if (doctorName) doctorName.textContent = result.session.practitioner_display || "";
        if (sessionTitle) {
          sessionTitle.textContent = this.isDoctor
            ? (result.session.patient_display || result.session.patient)
            : (result.session.practitioner_display || this.t("session"));
        }
        if (this.isDoctor) {
          const endLabel = document.getElementById("hc-end-label");
          if (endLabel) endLabel.textContent = this.lang === "ar" ? "إنهاء الاستشارة" : "End Consultation";
        }
      } catch (e) {
        console.error("Failed to load session context:", e);
      }
    },

    initRealtime() {
      if (!this.sessionId || typeof frappe.realtime === "undefined") return;
      frappe.realtime.on("telemedicine_chat", (payload) => {
        if (payload.session_id === this.sessionId) {
          this.appendChatMessage(payload.message, payload.message.sender === frappe.session.user ? "sent" : "received");
        }
      });
      frappe.realtime.on("telemedicine_session", (payload) => {
        if (payload.session_id === this.sessionId && payload.event === "session_completed") {
          this.updateSessionStatus("disconnected");
        }
      });
    },

    async loadChatHistory() {
      if (!this.sessionId) return;
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_socket.get_session_chat_messages",
          args: { session_id: this.sessionId },
        });
        const result = this.apiResult(r);
        (result.messages || []).forEach((msg) => {
          this.appendChatMessage(msg, msg.sender === frappe.session.user ? "sent" : "received");
        });
      } catch (e) {
        console.error("Failed to load chat history:", e);
      }
    },

    appendChatMessage(msg, direction) {
      const messages = document.getElementById("hc-chat-messages");
      if (!messages) return;
      const msgDiv = document.createElement("div");
      msgDiv.className = `hc-chat-message ${direction}`;
      msgDiv.innerHTML = `<strong>${msg.sender_name || msg.sender || ""}</strong><br>${msg.message || msg.body || ""}`;
      messages.appendChild(msgDiv);
      messages.scrollTop = messages.scrollHeight;
    },

    getSessionIdFromUrl() {
      const params = new URLSearchParams(window.location.search);
      return params.get("session_id");
    },

    async initVideoCall() {
      // Initialize WebRTC video call
      console.log("Initializing video call for session:", this.sessionId);
      
      if (!this.sessionId) {
        this.updateSessionStatus("error");
        return;
      }

      this.updateSessionStatus("connecting");
      
      // Get session info and token
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.join_telemedicine_session",
          args: { session_id: this.sessionId }
        });
        
        const result = this.apiResult(r);
        if (result.success) {
          this.roomId = result.room_id;
          this.token = result.token;
          this.sessionType = result.session_type;
          this.jitsiConfig = result.jitsi || {};
          this.initializeWebRTC();
        } else {
          this.updateSessionStatus("error");
          alert(result.error || "Failed to join session");
        }
      } catch (e) {
        console.error("Failed to join session:", e);
        this.updateSessionStatus("error");
      }
    },

    initializeWebRTC() {
      const jitsi = this.jitsiConfig || {};
      const domain = jitsi.domain || "meet.jit.si";
      const roomName = jitsi.room_name || this.roomId;
      const videoArea = document.getElementById("hc-video-area");
      if (!videoArea || !roomName) return;

      let container = document.getElementById("hc-jitsi-container");
      if (!container) {
        container = document.createElement("div");
        container.id = "hc-jitsi-container";
        container.style.width = "100%";
        container.style.height = "480px";
        videoArea.prepend(container);
      }
      container.style.display = "block";
      const videoGrid = videoArea.querySelector(".hc-video-grid");
      if (videoGrid) videoGrid.style.display = "none";

      const startJitsi = () => {
        if (typeof JitsiMeetExternalAPI === "undefined") {
          this.setupLocalVideo();
          this.updateSessionStatus("connected");
          return;
        }
        const options = {
          roomName,
          parentNode: container,
          userInfo: { displayName: jitsi.display_name || "Participant" },
          configOverwrite: jitsi.config_overwrite || {},
        };
        if (jitsi.jwt) options.jwt = jitsi.jwt;
        if (jitsi.ice_servers && jitsi.ice_servers.length) {
          options.configOverwrite = options.configOverwrite || {};
          options.configOverwrite.iceServers = jitsi.ice_servers;
        }
        this.jitsiApi = new JitsiMeetExternalAPI(domain, options);
        this.jitsiApi.addListener("videoConferenceJoined", () => this.updateSessionStatus("connected"));
        this.jitsiApi.addListener("videoConferenceLeft", () => this.updateSessionStatus("disconnected"));
      };

      if (typeof JitsiMeetExternalAPI === "undefined") {
        const script = document.createElement("script");
        script.src = `https://${domain}/external_api.js`;
        script.onload = startJitsi;
        script.onerror = () => {
          this.setupLocalVideo();
          this.updateSessionStatus("connected");
        };
        document.head.appendChild(script);
      } else {
        startJitsi();
      }
    },

    async setupLocalVideo() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true
        });
        
        const localVideo = document.getElementById("hc-patient-video");
        if (localVideo && localVideo.tagName === "VIDEO") {
          localVideo.srcObject = stream;
        }
        
        this.localStream = stream;
      } catch (e) {
        console.error("Failed to get local media:", e);
      }
    },

    setupRemoteVideo() {
      // Remote video will be set up when peer connects
      console.log("Remote video setup ready");
    },

    updateSessionStatus(status) {
      const indicator = document.getElementById("hc-status-indicator");
      const text = document.getElementById("hc-status-text");
      
      if (indicator) {
        indicator.className = "hc-status-indicator " + status;
      }
      if (text) {
        text.textContent = this.t(status);
      }
    },

    async loadPatientRecords() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_telemedicine_session",
          args: { session_id: this.sessionId },
        });
        const result = this.apiResult(r);
        if (!result.success || !result.session) return;

        const patientId = result.session.patient;
        const summaryR = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_patient_clinical_summary",
          args: { patient_id: patientId },
        });
        const summary = this.apiResult(summaryR).summary || {};
        const vitals = summary.readings || [];
        const vitalsGrid = document.getElementById("hc-vitals-grid");
        if (vitalsGrid) {
          vitalsGrid.innerHTML = vitals.slice(0, 4).map((v) => `
            <div class="hc-vital-item">
              <div class="hc-vital-value">${v.value} ${v.unit || ""}</div>
              <div class="hc-vital-label">${v.metric_type}</div>
            </div>
          `).join("") || `<div class="hc-vital-item"><div class="hc-vital-value">--</div><div class="hc-vital-label">N/A</div></div>`;
        }

        const medsList = document.getElementById("hc-medications-list");
        if (medsList) {
          const meds = summary.medications || [];
          medsList.innerHTML = meds.length
            ? meds.map(m => `<div class="hc-record-item">${m.drug_name} — ${m.dose || ""} ${m.frequency || ""}</div>`).join("")
            : `<div class="hc-record-item">${this.lang === "ar" ? "لا توجد أدوية" : "No medications"}</div>`;
        }

        const allergiesList = document.getElementById("hc-allergies-list");
        if (allergiesList) {
          allergiesList.innerHTML = summary.allergies
            ? `<div class="hc-record-item">${summary.allergies}</div>`
            : `<div class="hc-record-item">${this.lang === "ar" ? "لا توجد حساسية" : "No allergies"}</div>`;
        }

        const conditionsList = document.getElementById("hc-conditions-list");
        if (conditionsList) {
          const conditions = summary.conditions || [];
          conditionsList.innerHTML = conditions.length
            ? conditions.map(c => `<div class="hc-record-item">${c.clinical_description || c.icd10_code || c.name}</div>`).join("")
            : `<div class="hc-record-item">${this.lang === "ar" ? "لا توجد أمراض مزمنة" : "No conditions"}</div>`;
        }
      } catch (e) {
        console.error("Failed to load patient records:", e);
      }
    },

    initDoctorTools() {
      const recordsPanel = document.getElementById("hc-records-panel");
      if (!recordsPanel || document.getElementById("hc-doctor-rx-section")) return;

      const section = document.createElement("div");
      section.id = "hc-doctor-rx-section";
      section.className = "hc-record-section";
      section.innerHTML = `
        <h4 id="hc-rx-title">${this.lang === "ar" ? "وصفة طبية" : "E-Prescription"}</h4>
        <div class="hc-field"><label>${this.lang === "ar" ? "دواء" : "Medication"}</label><input id="hc-rx-medication" class="form-control" /></div>
        <div class="hc-field"><label>${this.lang === "ar" ? "جرعة" : "Dosage"}</label><input id="hc-rx-dosage" class="form-control" /></div>
        <div class="hc-field"><label>${this.lang === "ar" ? "تكرار" : "Frequency"}</label><input id="hc-rx-frequency" class="form-control" placeholder="1x daily" /></div>
        <div class="hc-field"><label>${this.lang === "ar" ? "مدة" : "Duration"}</label><input id="hc-rx-duration" class="form-control" placeholder="7 days" /></div>
        <div class="hc-field"><label>${this.lang === "ar" ? "ملاحظات سريرية" : "Clinical notes"}</label><textarea id="hc-doctor-notes" class="form-control" rows="3">${this.sessionData?.clinical_notes || ""}</textarea></div>
        <div id="hc-rx-list" class="hc-medications-list"></div>
        <button class="hc-btn hc-btn-outline" id="hc-add-rx">${this.lang === "ar" ? "إضافة دواء" : "Add medication"}</button>
      `;
      recordsPanel.querySelector(".hc-records-content")?.appendChild(section);

      document.getElementById("hc-add-rx")?.addEventListener("click", () => this.addPrescriptionRow());
      this.renderPrescriptionList();
    },

    addPrescriptionRow() {
      const medication = document.getElementById("hc-rx-medication")?.value?.trim();
      if (!medication) return;
      this.sessionPrescriptions.push({
        medication,
        dosage: document.getElementById("hc-rx-dosage")?.value || "",
        frequency: document.getElementById("hc-rx-frequency")?.value || "",
        duration: document.getElementById("hc-rx-duration")?.value || "",
        instructions: "",
      });
      ["hc-rx-medication", "hc-rx-dosage", "hc-rx-frequency", "hc-rx-duration"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = "";
      });
      this.renderPrescriptionList();
    },

    renderPrescriptionList() {
      const list = document.getElementById("hc-rx-list");
      if (!list) return;
      list.innerHTML = (this.sessionPrescriptions || []).map((rx, i) => `
        <div class="hc-record-item">${rx.medication} — ${rx.dosage} ${rx.frequency} (${rx.duration})
          <button type="button" class="hc-btn hc-btn-sm hc-btn-outline" onclick="TelemedicinePortal.removePrescription(${i})">×</button>
        </div>
      `).join("") || `<div class="hc-record-item">${this.lang === "ar" ? "لا توجد وصفات" : "No prescriptions yet"}</div>`;
    },

    removePrescription(index) {
      this.sessionPrescriptions.splice(index, 1);
      this.renderPrescriptionList();
    },

    async saveSessionPrescriptions() {
      if (!this.sessionId || !this.sessionPrescriptions?.length) return;
      await frappe.call({
        method: "omnexa_healthcare.api.telemedicine.save_session_prescriptions",
        args: { session_id: this.sessionId, items: this.sessionPrescriptions },
      });
    },

    initChat() {
      const input = document.getElementById("hc-chat-input");
      const sendBtn = document.getElementById("hc-send-message");
      const messages = document.getElementById("hc-chat-messages");

      if (sendBtn) {
        sendBtn.addEventListener("click", () => this.sendMessage());
      }
      if (input) {
        input.addEventListener("keypress", (e) => {
          if (e.key === "Enter") this.sendMessage();
        });
      }
    },

    async sendMessage() {
      const input = document.getElementById("hc-chat-input");
      const text = input.value.trim();
      if (!text || !this.sessionId) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_socket.send_session_chat_message",
          args: { session_id: this.sessionId, message: text },
        });
        const result = this.apiResult(r);
        if (result.success) {
          this.appendChatMessage(result.message, "sent");
          input.value = "";
        }
      } catch (e) {
        console.error("Failed to send chat message:", e);
      }
    },

    initControls() {
      const micBtn = document.getElementById("hc-mic-btn");
      const cameraBtn = document.getElementById("hc-camera-btn");
      const screenBtn = document.getElementById("hc-screen-btn");
      const whiteboardBtn = document.getElementById("hc-whiteboard-btn");
      const fileBtn = document.getElementById("hc-file-btn");
      const settingsBtn = document.getElementById("hc-settings-btn");
      const endBtn = document.getElementById("hc-end-call");

      if (micBtn) micBtn.addEventListener("click", () => this.toggleMic());
      if (cameraBtn) cameraBtn.addEventListener("click", () => this.toggleCamera());
      if (screenBtn) screenBtn.addEventListener("click", () => this.shareScreen());
      if (whiteboardBtn) whiteboardBtn.addEventListener("click", () => this.openWhiteboard());
      if (fileBtn) fileBtn.addEventListener("click", () => this.openFileModal());
      if (settingsBtn) settingsBtn.addEventListener("click", () => this.openSettings());
      if (endBtn) endBtn.addEventListener("click", () => this.openEndModal());

      const toggleChat = document.getElementById("hc-toggle-chat");
      const toggleRecords = document.getElementById("hc-toggle-records");
      
      if (toggleChat) toggleChat.addEventListener("click", () => this.togglePanel("chat"));
      if (toggleRecords) toggleRecords.addEventListener("click", () => this.togglePanel("records"));
    },

    toggleMic() {
      const btn = document.getElementById("hc-mic-btn");
      btn.classList.toggle("active");
      btn.classList.toggle("inactive");
    },

    toggleCamera() {
      const btn = document.getElementById("hc-camera-btn");
      btn.classList.toggle("active");
      btn.classList.toggle("inactive");
    },

    shareScreen() {
      alert("Screen sharing would be implemented with WebRTC");
    },

    togglePanel(panel) {
      const chatPanel = document.getElementById("hc-chat-panel");
      const recordsPanel = document.getElementById("hc-records-panel");
      const sidePanel = document.getElementById("hc-side-panel");
      
      if (panel === "chat") {
        chatPanel.style.display = "flex";
        recordsPanel.style.display = "none";
      } else {
        chatPanel.style.display = "none";
        recordsPanel.style.display = "flex";
      }
      
      sidePanel.classList.add("open");
    },

    initModals() {
      // Whiteboard modal
      const closeWhiteboard = document.getElementById("hc-close-whiteboard");
      if (closeWhiteboard) {
        closeWhiteboard.addEventListener("click", () => this.closeModal("hc-whiteboard-modal"));
      }

      // File modal
      const closeFile = document.getElementById("hc-close-file");
      if (closeFile) {
        closeFile.addEventListener("click", () => this.closeModal("hc-file-modal"));
      }

      // Settings modal
      const closeSettings = document.getElementById("hc-close-settings");
      if (closeSettings) {
        closeSettings.addEventListener("click", () => this.closeModal("hc-settings-modal"));
      }

      // End modal
      const cancelEnd = document.getElementById("hc-cancel-end");
      const confirmEnd = document.getElementById("hc-confirm-end");
      if (cancelEnd) {
        cancelEnd.addEventListener("click", () => this.closeModal("hc-end-modal"));
      }
      if (confirmEnd) {
        confirmEnd.addEventListener("click", () => this.endSession());
      }

      // Rating stars
      const stars = document.querySelectorAll(".hc-star");
      stars.forEach(star => {
        star.addEventListener("click", () => {
          const rating = parseInt(star.dataset.rating, 10);
          this.selectedRating = rating;
          stars.forEach(s => s.classList.remove("active"));
          for (let i = 0; i < rating; i++) {
            stars[i].classList.add("active");
          }
        });
      });
    },

    openWhiteboard() {
      document.getElementById("hc-whiteboard-modal").style.display = "flex";
    },

    openFileModal() {
      document.getElementById("hc-file-modal").style.display = "flex";
    },

    openSettings() {
      document.getElementById("hc-settings-modal").style.display = "flex";
    },

    openEndModal() {
      document.getElementById("hc-end-modal").style.display = "flex";
    },

    closeModal(id) {
      document.getElementById(id).style.display = "none";
    },

    endSession() {
      const feedback = document.getElementById("hc-feedback-text")?.value || "";
      const doctorNotes = document.getElementById("hc-doctor-notes")?.value || "";
      const rating = this.selectedRating || null;

      if (this.jitsiApi) {
        try {
          this.jitsiApi.dispose();
        } catch (e) {
          console.warn("Jitsi dispose failed:", e);
        }
      }

      const finish = () => {
        frappe.call({
          method: "omnexa_healthcare.api.telemedicine.end_telemedicine_session",
          args: {
            session_id: this.sessionId,
            data: {
              clinical_notes: this.isDoctor ? doctorNotes : feedback,
              patient_feedback: this.isDoctor ? feedback : undefined,
              rating: this.isDoctor ? undefined : rating,
              technical_quality: "Good",
            },
          },
          callback: (r) => {
            const result = this.apiResult(r);
            if (result.success) {
              window.location.href = this.isDoctor ? "/telemedicine-doctor" : "/telemedicine";
            } else {
              alert(result.error || "Failed to end session");
            }
          },
        });
      };

      if (this.isDoctor && this.sessionPrescriptions?.length) {
        this.saveSessionPrescriptions().then(finish).catch(finish);
      } else {
        finish();
      }
    },
  };
})();
