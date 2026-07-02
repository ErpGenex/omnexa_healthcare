/* global frappe */
(function () {
  const STORAGE_LANG = "hc_telemedicine_doctor_lang";

  window.TelemedicineDoctor = {
    lang: localStorage.getItem(STORAGE_LANG) || "ar",
    page: null,
    config: null,
    practitionerId: null,
    scheduleSessions: [],
    calendarYear: new Date().getFullYear(),
    calendarMonth: new Date().getMonth(),
    patientsCache: [],
    socket: null,

    apiResult(response) {
      return response.message || {};
    },

    async resolvePractitioner() {
      if (this.practitionerId) return this.practitionerId;
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_current_practitioner",
        });
        const result = this.apiResult(r);
        if (result.success) {
          this.practitionerId = result.practitioner_id;
          const title = document.getElementById("hc-welcome-title");
          if (title && result.practitioner_name) {
            title.textContent = `${this.lang === "ar" ? "مرحباً،" : "Welcome,"} ${result.practitioner_name}`;
          }
        }
      } catch (e) {
        console.error("Failed to resolve practitioner:", e);
      }
      return this.practitionerId;
    },

    init(page) {
      this.page = page;
      const pageKey = String(page || "").replace(/-/g, "_");
      console.log("TelemedicineDoctor.init called with page:", page);
      console.log("Page key after replacement:", pageKey);
      this.loadConfig().then(async () => {
        await this.resolvePractitioner();
        this.applyTheme();
        this.renderChrome();
        this.initRealtime();
        const initFn = this[`init_${pageKey}`];
        console.log("Looking for init_" + pageKey);
        console.log("Function exists:", typeof initFn === "function");
        if (typeof initFn === "function") {
          initFn.call(this);
        } else {
          console.warn("TelemedicineDoctor: no handler for page", page);
        }
      });
    },

    openDeskRoute(path) {
      const target = `/app/${path}`;
      if (window.top && window.top !== window) {
        window.top.location.href = target;
      } else {
        window.location.href = target;
      }
    },

    initRealtime() {
      if (typeof TelemedicineSocket === "undefined" || typeof frappe === "undefined") return;
      this.socket = new TelemedicineSocket();
      this.socket.connect(frappe.session.user, null).then(() => {
        this.socket.subscribeToQueue(this.practitionerId);
        this.socket.on("queue_update", () => {
          if (this.page === "queue" || this.page === "home") {
            this.page === "queue" ? this.loadQueueList() : this.loadQueue();
          }
        });
        this.socket.on("session_status", () => {
          if (this.page === "queue") this.loadQueueList();
        });
      });
    },

    t(key) {
      const map = {
        home: { ar: "الرئيسية", en: "Home" },
        queue: { ar: "قائمة الانتظار", en: "Queue" },
        schedule: { ar: "الجدول", en: "Schedule" },
        patients: { ar: "المرضى", en: "Patients" },
        records: { ar: "السجلات", en: "Records" },
        prescriptions: { ar: "الوصفات", en: "Prescriptions" },
        reports: { ar: "التقارير", en: "Reports" },
        settings: { ar: "الإعدادات", en: "Settings" },
        refresh: { ar: "تحديث", en: "Refresh" },
        loading: { ar: "جاري التحميل...", en: "Loading..." },
        no_patients: { ar: "لا يوجد مرضى", en: "No patients" },
        no_appointments: { ar: "لا توجد مواعيد", en: "No appointments" },
        waiting: { ar: "في الانتظار", en: "Waiting" },
        in_consultation: { ar: "جاري الاستشارة", en: "In Consultation" },
        completed: { ar: "مكتمل", en: "Completed" },
        start_consultation: { ar: "بدء الاستشارة", en: "Start Consultation" },
        view_details: { ar: "عرض التفاصيل", en: "View Details" },
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
          primary_color: "#0066cc",
          secondary_color: "#004499"
        };
      }
    },

    applyTheme() {
      const site = document.querySelector(".hc-telemedicine-doctor");
      if (!site) return;
      
      if (this.config.primary_color) {
        site.style.setProperty("--hc-tele-primary", this.config.primary_color);
      }
      
      site.dir = this.lang === "ar" ? "rtl" : "ltr";
    },

    renderChrome() {
      this.renderHeader();
      this.renderFooter();
    },

    renderHeader() {
      const header = document.getElementById("hc-header");
      if (!header) return;

      const nav = [
        { key: "home", href: "/telemedicine-doctor" },
        { key: "queue", href: "/telemedicine-doctor/queue" },
        { key: "schedule", href: "/telemedicine-doctor/schedule" },
        { key: "patients", href: "/telemedicine-doctor/patients" },
      ];

      header.innerHTML = `
        <div class="hc-wrap">
          <div class="hc-header-inner">
            <div class="hc-brand">
              <span>👨‍⚕️ ${this.t("home")}</span>
            </div>
            <nav class="hc-nav">
              ${nav.map(item => `
                <a href="${item.href}" class="${this.page === item.key ? 'active' : ''}">
                  ${this.t(item.key)}
                </a>
              `).join('')}
            </nav>
            <div class="hc-actions">
              <button class="hc-lang" onclick="TelemedicineDoctor.toggleLang()">
                ${this.lang === "ar" ? "EN" : "عربي"}
              </button>
            </div>
            <button class="hc-mobile-toggle" onclick="TelemedicineDoctor.toggleMobileNav()">
              ☰
            </button>
          </div>
        </div>
      `;
    },

    renderFooter() {
      const footer = document.getElementById("hc-footer");
      if (!footer) return;

      footer.innerHTML = `
        <div class="hc-wrap">
          <div style="text-align: center; padding: 20px 0; border-top: 1px solid #e6eef6;">
            <p>© 2026 Telemedicine Doctor Portal. All rights reserved.</p>
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
      this.loadDashboardStats();
      this.loadUpcomingAppointments();
      this.loadQueue();
    },

    async loadDashboardStats() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_practitioner_stats",
          args: { practitioner_id: this.practitionerId }
        });
        
        const result = this.apiResult(r);
        if (result.success) {
          const stats = result.stats;
          document.getElementById("hc-patients-today").textContent = stats.today_sessions || 0;
          document.getElementById("hc-consultations-today").textContent = stats.completed_sessions || 0;
          document.getElementById("hc-avg-rating").textContent = stats.average_rating || "0.0";
          document.getElementById("hc-revenue-today").textContent = "0";
        }
      } catch (e) {
        console.error("Failed to load stats:", e);
      }
    },

    async loadUpcomingAppointments() {
      const list = document.getElementById("hc-appointments-list");
      if (!list) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_practitioner_sessions",
          args: {
            practitioner_id: this.practitionerId,
            status: "Scheduled",
          },
        });
        
        const result = this.apiResult(r);
        if (result.success && result.sessions.length > 0) {
          list.innerHTML = result.sessions.slice(0, 5).map(s => `
            <div class="hc-appointment-item">
              <div class="hc-appointment-time">${s.scheduled_datetime}</div>
              <div class="hc-appointment-patient">${s.patient_display}</div>
              <div class="hc-appointment-type">${s.session_type}</div>
            </div>
          `).join('');
        }
      } catch (e) {
        console.error("Failed to load appointments:", e);
      }
    },

    async loadQueue() {
      const list = document.getElementById("hc-queue-list");
      const count = document.getElementById("hc-queue-count");
      if (!list) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_doctor_queue",
          args: { practitioner_id: this.practitionerId }
        });
        
        const result = this.apiResult(r);
        if (result.success) {
          const queue = result.queue;
          if (count) count.textContent = queue.length;
          
          if (queue.length > 0) {
            list.innerHTML = queue.map(q => `
              <div class="hc-queue-item">
                <div class="hc-queue-position">#${q.queue_position}</div>
                <div class="hc-queue-patient">${q.patient}</div>
                <div class="hc-queue-wait">${q.estimated_wait} min</div>
                <button class="hc-btn hc-btn-sm hc-btn-primary" onclick="TelemedicineDoctor.callPatient('${q.session_id}')">
                  ${this.t("start_consultation")}
                </button>
              </div>
            `).join('');
          }
        }
      } catch (e) {
        console.error("Failed to load queue:", e);
      }
    },

    async callPatient(sessionId) {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.start_telemedicine_session",
          args: { session_id: sessionId },
        });
        
        const result = this.apiResult(r);
        if (result.success) {
          window.location.href = `/telemedicine/session?session_id=${sessionId}`;
        } else {
          alert(result.error || "Failed to start consultation");
        }
      } catch (e) {
        console.error("Failed to call patient:", e);
        alert("Failed to call patient");
      }
    },

    // Queue Page
    init_queue() {
      this.loadQueueList();
      this.initQueueActions();
    },

    async loadQueueList() {
      const waitingList = document.getElementById("hc-waiting-list");
      const waitingCount = document.getElementById("hc-waiting-count");
      const consultingCount = document.getElementById("hc-consulting-count");
      
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_doctor_queue",
          args: { practitioner_id: this.practitionerId }
        });
        
        const result = this.apiResult(r);
        if (result.success) {
          const queue = result.queue;
          const waiting = queue.filter(q => q.status === "Waiting");
          const consulting = queue.filter(q => q.status === "In Progress");
          
          if (waitingCount) waitingCount.textContent = waiting.length;
          if (consultingCount) consultingCount.textContent = consulting.length;
          
          if (waitingList && waiting.length > 0) {
            waitingList.innerHTML = waiting.map(q => `
              <div class="hc-patient-card">
                <div class="hc-patient-info">
                  <div class="hc-patient-name">${q.patient}</div>
                  <div class="hc-patient-meta">
                    <span>${q.session_type}</span>
                    <span>•</span>
                    <span>Position: ${q.queue_position}</span>
                    <span>•</span>
                    <span>Wait: ${q.estimated_wait} min</span>
                  </div>
                </div>
                <button class="hc-btn hc-btn-primary" onclick="TelemedicineDoctor.callPatient('${q.session_id}')">
                  ${this.t("start_consultation")}
                </button>
              </div>
            `).join('');
          }
        }
      } catch (e) {
        console.error("Failed to load queue:", e);
      }
    },

    initQueueActions() {
      const refreshBtn = document.getElementById("hc-refresh-queue");
      if (refreshBtn) {
        refreshBtn.addEventListener("click", () => this.loadQueueList());
      }

      // Call patient buttons
      document.querySelectorAll(".hc-call-patient").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const sessionId = e.target.getAttribute("data-session-id");
          this.callPatient(sessionId);
        });
      });
    },

    // Reports Page
    init_reports() {
      this.loadReports();
    },

    async loadReports() {
      const reportsGrid = document.getElementById("hc-reports-grid");
      if (!reportsGrid) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_practitioner_stats",
          args: { practitioner_id: this.practitionerId },
        });
        const result = this.apiResult(r);
        const stats = result.stats || {};
        const reports = [
          { title: "استشارات اليوم", value: String(stats.today_sessions || 0), trend: "+0%", icon: "📹" },
          { title: "رضا المرضى", value: `${stats.average_rating || 0}/5`, trend: "+0%", icon: "⭐" },
          { title: "قائمة الانتظار", value: String(stats.queue_count || 0), trend: "0", icon: "⏰" },
          { title: "الجلسات المكتملة", value: String(stats.completed_sessions || 0), trend: "+0%", icon: "💰" },
        ];
        reportsGrid.innerHTML = reports.map(r => `
          <div class="hc-card hc-report-card">
            <div class="hc-report-icon">${r.icon}</div>
            <div class="hc-report-title">${r.title}</div>
            <div class="hc-report-value">${r.value}</div>
            <div class="hc-report-trend positive">${r.trend}</div>
          </div>
        `).join('');
      } catch (e) {
        console.error("Failed to load reports:", e);
      }
    },

    // Prescriptions Page
    init_prescriptions() {
      this.loadPrescriptions();
    },

    async loadPrescriptions(filters = {}) {
      const table = document.getElementById("hc-prescriptions-table");
      if (!table) return;

      try {
        const args = { practitioner_id: this.practitionerId, status: filters.status || "Completed" };
        if (filters.date) {
          args.from_date = filters.date;
          args.to_date = filters.date;
        }
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_practitioner_sessions",
          args,
        });
        const result = this.apiResult(r);
        let sessions = result.sessions || [];
        if (filters.patient) {
          sessions = sessions.filter(s => s.patient === filters.patient);
        }
        const tbody = table.querySelector("tbody");
        if (tbody) {
          if (!sessions.length) {
            tbody.innerHTML = `<tr><td colspan="5">${this.t("no_patients")}</td></tr>`;
          } else {
            tbody.innerHTML = sessions.map(s => `
              <tr>
                <td>${s.patient_display || s.patient}</td>
                <td>${s.session_type}</td>
                <td>${(s.scheduled_datetime || "").split(" ")[0]}</td>
                <td><span class="hc-badge hc-badge-success">${this.t("completed")}</span></td>
                <td>
                  <button class="hc-btn hc-btn-sm hc-btn-outline hc-view-prescription" data-rx-id="${s.name}">عرض</button>
                </td>
              </tr>
            `).join("");
          }
        }
      } catch (e) {
        console.error("Failed to load prescriptions:", e);
      }

      this.initPrescriptionsActions();
    },

    initPrescriptionsActions() {
      // View prescription button
      document.querySelectorAll(".hc-view-prescription").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const rxId = e.target.getAttribute("data-rx-id");
          this.viewPrescription(rxId);
        });
      });

      // Filter button
      const filterBtn = document.getElementById("hc-filter-prescriptions");
      if (filterBtn) {
        filterBtn.addEventListener("click", () => this.filterPrescriptions());
      }
    },

    viewPrescription(rxId) {
      window.location.href = `/app/healthcare-telemedicine-session/${rxId}`;
    },

    filterPrescriptions() {
      this.loadPrescriptions({
        patient: document.getElementById("hc-filter-patient")?.value,
        date: document.getElementById("hc-filter-date")?.value,
        status: document.getElementById("hc-filter-status")?.value,
      });
    },

    // Records Page
    init_records() {
      this.loadRecords();
    },

    async loadRecords(filters = {}) {
      const table = document.getElementById("hc-records-table");
      if (!table) return;

      try {
        const args = { practitioner_id: this.practitionerId, status: "Completed" };
        if (filters.date) {
          args.from_date = filters.date;
          args.to_date = filters.date;
        }
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_practitioner_sessions",
          args,
        });
        const result = this.apiResult(r);
        let records = result.sessions || [];
        if (filters.patient) records = records.filter(r => r.patient === filters.patient);
        if (filters.type) records = records.filter(r => (r.session_type || "").toLowerCase() === filters.type.toLowerCase());
        const tbody = table.querySelector("tbody");
        if (tbody) {
          if (!records.length) {
            tbody.innerHTML = `<tr><td colspan="5">${this.t("no_patients")}</td></tr>`;
          } else {
            tbody.innerHTML = records.map(r => `
              <tr>
                <td>${r.patient_display || r.patient}</td>
                <td>${r.session_type}</td>
                <td>${(r.scheduled_datetime || "").split(" ")[0]}</td>
                <td>${r.clinical_notes || "-"}</td>
                <td>
                  <button class="hc-btn hc-btn-sm hc-btn-outline hc-view-record" data-record-id="${r.name}">عرض</button>
                </td>
              </tr>
            `).join("");
          }
        }
      } catch (e) {
        console.error("Failed to load records:", e);
      }

      this.initRecordsActions();
    },

    initRecordsActions() {
      // View record button
      document.querySelectorAll(".hc-view-record").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const recordId = e.target.getAttribute("data-record-id");
          this.viewRecord(recordId);
        });
      });

      // Filter button
      const filterBtn = document.getElementById("hc-filter-records");
      if (filterBtn) {
        filterBtn.addEventListener("click", () => this.filterRecords());
      }
    },

    viewRecord(recordId) {
      window.location.href = `/app/healthcare-telemedicine-session/${recordId}`;
    },

    filterRecords() {
      this.loadRecords({
        patient: document.getElementById("hc-filter-patient")?.value,
        type: document.getElementById("hc-filter-type")?.value,
        date: document.getElementById("hc-filter-date")?.value,
      });
    },

    // Patients Page
    init_patients() {
      this.loadPatients();
    },

    async loadPatients() {
      const table = document.getElementById("hc-patients-table");
      if (!table) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_patients",
          args: { limit: 100 },
        });
        const result = this.apiResult(r);
        if (!result.success && result.error) {
          alert(result.error);
          return;
        }

        const patients = result.patients || [];
        this.patientsCache = patients;
        const tbody = table.querySelector("tbody");
        if (tbody) {
          if (!patients.length) {
            tbody.innerHTML = `<tr><td colspan="5">${this.t("no_patients")}</td></tr>`;
          } else {
            tbody.innerHTML = patients.map(p => `
              <tr>
                <td>${p.full_name || p.name}</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>
                  <button type="button" class="hc-btn hc-btn-sm hc-btn-outline hc-view-patient" data-patient-id="${p.name}">${this.t("view_details")}</button>
                  <button type="button" class="hc-btn hc-btn-sm hc-btn-primary hc-start-consultation" data-patient-id="${p.name}">${this.t("start_consultation")}</button>
                </td>
              </tr>
            `).join("");
          }
        }
      } catch (e) {
        console.error("Failed to load patients:", e);
        alert(this.lang === "ar" ? "تعذر تحميل المرضى" : "Failed to load patients");
      }

      this.initPatientsActions();
    },

    initPatientsActions() {
      document.querySelectorAll(".hc-view-patient").forEach(btn => {
        btn.addEventListener("click", (e) => {
          this.viewPatient(e.currentTarget.getAttribute("data-patient-id"));
        });
      });

      document.querySelectorAll(".hc-start-consultation").forEach(btn => {
        btn.addEventListener("click", (e) => {
          this.startConsultation(e.currentTarget.getAttribute("data-patient-id"));
        });
      });

      const filterBtn = document.getElementById("hc-filter-patients");
      if (filterBtn) {
        filterBtn.addEventListener("click", () => this.filterPatients());
      }
    },

    viewPatient(patientId) {
      if (!patientId) return;
      this.openDeskRoute(`healthcare-patient/${patientId}`);
    },

    async startConsultation(patientId) {
      if (!patientId) return;
      const practitioner = await this.resolvePractitioner();
      if (!practitioner) {
        alert(this.lang === "ar" ? "لم يتم ربط حسابك بطبيب" : "No practitioner linked to your account");
        return;
      }

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.start_doctor_consultation",
          args: {
            patient: patientId,
            practitioner,
            session_type: "Video",
          },
        });
        const result = this.apiResult(r);
        if (result.success) {
          window.location.href = `/telemedicine/session?session_id=${result.session_id}`;
        } else {
          alert(result.error || (this.lang === "ar" ? "فشل بدء الاستشارة" : "Failed to start consultation"));
        }
      } catch (e) {
        console.error("Failed to start consultation:", e);
        alert(this.lang === "ar" ? "فشل بدء الاستشارة" : "Failed to start consultation");
      }
    },

    filterPatients() {
      const search = (document.getElementById("hc-search-patient")?.value || "").trim().toLowerCase();
      const table = document.getElementById("hc-patients-table");
      const tbody = table?.querySelector("tbody");
      if (!tbody) return;

      let patients = this.patientsCache || [];
      if (search) {
        patients = patients.filter(p =>
          (p.full_name || p.name || "").toLowerCase().includes(search)
        );
      }

      if (!patients.length) {
        tbody.innerHTML = `<tr><td colspan="5">${this.t("no_patients")}</td></tr>`;
        return;
      }

      tbody.innerHTML = patients.map(p => `
        <tr>
          <td>${p.full_name || p.name}</td>
          <td>-</td>
          <td>${p.gender || "-"}</td>
          <td>${p.birth_date || "-"}</td>
          <td>
            <button class="hc-btn hc-btn-sm hc-btn-outline hc-view-patient" data-patient-id="${p.name}">عرض</button>
            <button class="hc-btn hc-btn-sm hc-btn-primary hc-start-consultation" data-patient-id="${p.name}">استشارة</button>
          </td>
        </tr>
      `).join("");
      this.initPatientsActions();
    },

    // New Patient Page
    init_patient_new() {
      console.log("init_patient_new called");
      this.initPatientForm();
    },

    // Alternative name for page key replacement
    init_patientnew() {
      console.log("init_patientnew called");
      this.initPatientForm();
    },

    initPatientForm() {
      const form = document.getElementById("hc-new-patient-form");
      console.log("Form element:", form);
      if (form) {
        form.addEventListener("submit", (e) => {
          console.log("Form submit event triggered");
          e.preventDefault();
          this.savePatient();
        });
      } else {
        console.error("Form not found!");
      }
    },

    async savePatient() {
      console.log("savePatient called");
      const name = document.getElementById("hc-patient-name")?.value;
      const dob = document.getElementById("hc-patient-dob")?.value;
      const gender = document.getElementById("hc-patient-gender")?.value;

      console.log("Form values:", { name, dob, gender });

      if (!name || !dob || !gender) {
        alert(this.lang === "ar" ? "يرجى ملء جميع الحقول المطلوبة" : "Please fill all required fields");
        return;
      }

      const practitioner = await this.resolvePractitioner();
      console.log("Practitioner:", practitioner);

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.create_telemedicine_patient",
          args: {
            data: {
              full_name: name,
              birth_date: dob,
              gender,
              phone: document.getElementById("hc-patient-phone")?.value,
              email: document.getElementById("hc-patient-email")?.value,
              address: document.getElementById("hc-patient-address")?.value,
              city: document.getElementById("hc-patient-city")?.value,
              area: document.getElementById("hc-patient-area")?.value,
              allergies: document.getElementById("hc-patient-allergies")?.value,
              practitioner,
            },
          },
        });
        console.log("API response:", r);
        const result = this.apiResult(r);
        console.log("Parsed result:", result);
        if (result.success) {
          alert(this.lang === "ar" ? "تم حفظ المريض بنجاح" : "Patient saved successfully");
          window.location.href = "/telemedicine-doctor/patients";
        } else {
          alert(result.error || (this.lang === "ar" ? "فشل حفظ المريض" : "Failed to save patient"));
        }
      } catch (e) {
        console.error("Failed to save patient:", e);
        alert(this.lang === "ar" ? "فشل حفظ المريض" : "Failed to save patient");
      }
    },

    // Schedule Page
    init_schedule() {
      this.loadSchedule();
    },

    async loadSchedule(filters = {}) {
      const table = document.getElementById("hc-schedule-table");
      if (!table) return;

      try {
        const args = { practitioner_id: this.practitionerId };
        if (filters.status) {
          const statusMap = {
            scheduled: "Scheduled",
            completed: "Completed",
            cancelled: "Cancelled",
            "no-show": "No Show",
          };
          args.status = statusMap[filters.status] || filters.status;
        }
        if (filters.date) {
          args.from_date = filters.date;
          args.to_date = filters.date;
        }

        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine.get_practitioner_sessions",
          args,
        });
        const result = this.apiResult(r);
        this.scheduleSessions = result.sessions || [];
        const appointments = this.scheduleSessions;
        const tbody = table.querySelector("tbody");
        if (tbody) {
          if (!appointments.length) {
            tbody.innerHTML = `<tr><td colspan="5">${this.t("no_appointments")}</td></tr>`;
          } else {
            tbody.innerHTML = appointments.map(a => {
              const statusKey = (a.status || "Scheduled").toLowerCase().replace(" ", "-");
              const statusMap = {
                scheduled: { text: "مجدول", class: "hc-badge-info" },
                "in-progress": { text: "جاري", class: "hc-badge-warning" },
                completed: { text: "مكتمل", class: "hc-badge-success" },
                cancelled: { text: "ملغي", class: "hc-badge-danger" },
                "no-show": { text: "لم يحضر", class: "hc-badge-warning" },
              };
              const status = statusMap[statusKey] || { text: a.status, class: "hc-badge-secondary" };
              const time = a.scheduled_datetime ? String(a.scheduled_datetime).split(" ")[1] : "-";
              return `
                <tr>
                  <td>${time}</td>
                  <td>${a.patient_display || a.patient}</td>
                  <td>${a.session_type}</td>
                  <td><span class="hc-badge ${status.class}">${status.text}</span></td>
                  <td>
                    <button class="hc-btn hc-btn-sm hc-btn-outline hc-view-appointment" data-appointment-id="${a.name}">عرض</button>
                    ${a.status === "Scheduled" ? `<button class="hc-btn hc-btn-sm hc-btn-primary hc-start-appointment" data-appointment-id="${a.name}">بدء</button>` : ""}
                  </td>
                </tr>
              `;
            }).join("");
          }
        }
      } catch (e) {
        console.error("Failed to load schedule:", e);
      }

      this.initCalendar();
      this.initScheduleActions();
    },

    initScheduleActions() {
      // View appointment button
      document.querySelectorAll(".hc-view-appointment").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const appointmentId = e.target.getAttribute("data-appointment-id");
          this.viewAppointment(appointmentId);
        });
      });

      // Start appointment button
      document.querySelectorAll(".hc-start-appointment").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const appointmentId = e.target.getAttribute("data-appointment-id");
          this.startAppointment(appointmentId);
        });
      });

      // Filter button
      const filterBtn = document.getElementById("hc-filter-schedule");
      if (filterBtn) {
        filterBtn.addEventListener("click", () => this.filterSchedule());
      }

      // Calendar navigation
      const prevMonthBtn = document.getElementById("hc-prev-month");
      const nextMonthBtn = document.getElementById("hc-next-month");
      if (prevMonthBtn) {
        prevMonthBtn.addEventListener("click", () => {
          this.calendarMonth -= 1;
          if (this.calendarMonth < 0) {
            this.calendarMonth = 11;
            this.calendarYear -= 1;
          }
          this.initCalendar();
        });
      }
      if (nextMonthBtn) {
        nextMonthBtn.addEventListener("click", () => {
          this.calendarMonth += 1;
          if (this.calendarMonth > 11) {
            this.calendarMonth = 0;
            this.calendarYear += 1;
          }
          this.initCalendar();
        });
      }
    },

    viewAppointment(appointmentId) {
      window.location.href = `/telemedicine/session?session_id=${appointmentId}`;
    },

    startAppointment(appointmentId) {
      this.callPatient(appointmentId);
    },

    filterSchedule() {
      this.loadSchedule({
        date: document.getElementById("hc-filter-date")?.value,
        status: document.getElementById("hc-filter-status")?.value,
      });
    },

    initCalendar() {
      const calendarGrid = document.getElementById("hc-calendar-grid");
      if (!calendarGrid) return;

      const year = this.calendarYear;
      const month = this.calendarMonth;
      const today = new Date();
      const firstDay = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();

      const appointmentDays = new Set(
        (this.scheduleSessions || [])
          .map(s => String(s.scheduled_datetime || "").split(" ")[0])
          .filter(d => {
            if (!d) return false;
            const parts = d.split("-").map(Number);
            return parts[0] === year && parts[1] === month + 1;
          })
          .map(d => parseInt(d.split("-")[2], 10))
      );

      const monthTitle = document.getElementById("hc-calendar-month");
      if (monthTitle) {
        const monthNames = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"];
        monthTitle.textContent = `${monthNames[month]} ${year}`;
      }

      let html = "";
      const dayNames = ["أحد", "إثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت"];
      dayNames.forEach(day => {
        html += `<div class="hc-calendar-day-header">${day}</div>`;
      });

      for (let i = 0; i < firstDay; i++) {
        html += `<div class="hc-calendar-day hc-calendar-day-empty"></div>`;
      }

      for (let day = 1; day <= daysInMonth; day++) {
        const isToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear();
        const hasAppointment = appointmentDays.has(day);
        html += `
          <div class="hc-calendar-day ${isToday ? "hc-calendar-day-today" : ""} ${hasAppointment ? "hc-calendar-day-has-appointment" : ""}">
            <span class="hc-calendar-day-number">${day}</span>
            ${hasAppointment ? '<span class="hc-calendar-day-dot"></span>' : ""}
          </div>
        `;
      }

      calendarGrid.innerHTML = html;
    },
  };
})();
