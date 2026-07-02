/* global frappe */
(function () {
  const STORAGE_LANG = "hc_telemedicine_admin_lang";

  window.TelemedicineAdmin = {
    lang: localStorage.getItem(STORAGE_LANG) || "ar",
    page: null,
    config: null,
    stats: {},

    apiResult(response) {
      return response.message || {};
    },

    init(page) {
      this.page = page;
      const pageKey = String(page || "").replace(/-/g, "_");
      this.loadConfig().then(() => {
        this.applyTheme();
        this.renderChrome();
        const initFn = this[`init_${pageKey}`];
        if (typeof initFn === "function") {
          initFn.call(this);
        } else {
          console.warn("TelemedicineAdmin: no handler for page", page);
        }
      });
    },

    t(key) {
      const map = {
        home: { ar: "الرئيسية", en: "Home" },
        dashboard: { ar: "لوحة التحكم", en: "Dashboard" },
        sessions: { ar: "الجلسات", en: "Sessions" },
        doctors: { ar: "الأطباء", en: "Doctors" },
        patients: { ar: "المرضى", en: "Patients" },
        reports: { ar: "التقارير", en: "Reports" },
        settings: { ar: "الإعدادات", en: "Settings" },
        refresh: { ar: "تحديث", en: "Refresh" },
        new_session: { ar: "جلسة جديدة", en: "New Session" },
        active_sessions: { ar: "جلسات نشطة", en: "Active Sessions" },
        today_sessions: { ar: "استشارات اليوم", en: "Today's Consultations" },
        satisfaction: { ar: "رضا المرضى", en: "Patient Satisfaction" },
        revenue: { ar: "الإيراد", en: "Revenue" },
        issues: { ar: "المشاكل", en: "Issues" },
        active_doctors: { ar: "أطباء نشطون", en: "Active Doctors" },
        system_health: { ar: "صحة النظام", en: "System Health" },
        quick_actions: { ar: "إجراءات سريعة", en: "Quick Actions" },
        alerts: { ar: "التنبيهات", en: "Alerts" },
        recent_activity: { ar: "النشاط الأخير", en: "Recent Activity" },
        manage_doctors: { ar: "إدارة الأطباء", en: "Manage Doctors" },
        manage_patients: { ar: "إدارة المرضى", en: "Manage Patients" },
        view_reports: { ar: "عرض التقارير", en: "View Reports" },
        system_settings: { ar: "إعدادات النظام", en: "System Settings" },
        view_all: { ar: "عرض الكل", en: "View All" },
        no_sessions: { ar: "لا توجد جلسات نشطة", en: "No active sessions" },
        no_alerts: { ar: "لا توجد تنبيهات", en: "No alerts" },
        connected: { ar: "متصل", en: "Connected" },
        disconnected: { ar: "منقطع", en: "Disconnected" },
      };
      return (map[key] && map[key][this.lang]) || key;
    },

    async loadConfig() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_config",
        });
        this.config = this.apiResult(r).config || this.apiResult(r) || {};
      } catch (e) {
        console.error("Failed to load config:", e);
        this.config = {};
      }
    },

    applyTheme() {
      const site = document.querySelector(".hc-telemedicine-admin");
      if (!site) return;
      
      if (this.config.primary_color) {
        site.style.setProperty("--hc-admin-primary", this.config.primary_color);
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
        { key: "dashboard", href: "/telemedicine-admin" },
        { key: "sessions", href: "/telemedicine-admin/sessions" },
        { key: "doctors", href: "/telemedicine-admin/doctors" },
        { key: "patients", href: "/telemedicine-admin/patients" },
        { key: "reports", href: "/telemedicine-admin/reports" },
        { key: "settings", href: "/telemedicine-admin/settings" },
      ];

      header.innerHTML = `
        <div class="hc-wrap">
          <div class="hc-header-inner">
            <div class="hc-brand">
              <span>🏥 ${this.t("dashboard")}</span>
            </div>
            <nav class="hc-nav">
              ${nav.map(item => `
                <a href="${item.href}" class="${this.page === item.key ? 'active' : ''}">
                  ${this.t(item.key)}
                </a>
              `).join('')}
            </nav>
            <div class="hc-actions">
              <button class="hc-lang" onclick="TelemedicineAdmin.toggleLang()">
                ${this.lang === "ar" ? "EN" : "عربي"}
              </button>
            </div>
            <button class="hc-mobile-toggle" onclick="TelemedicineAdmin.toggleMobileNav()">
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
            <p>© 2026 Telemedicine Admin Dashboard. All rights reserved.</p>
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
      this.loadStats();
      this.loadLiveSessions();
      this.loadSystemHealth();
      this.loadAlerts();
      this.initActions();
    },

    // Sessions Page
    init_sessions() {
      this.loadSessions();
      this.loadPractitioners();
      this.initSessionsActions();
    },

    // New Session Page
    init_new_session() {
      const dateInput = document.getElementById("hc-session-date");
      if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split("T")[0];
      }
      this.loadPatients();
      this.loadPractitioners();
      this.loadDepartments();
      this.initNewSessionActions();
    },

    // Doctors Page
    init_doctors() {
      this.loadDoctors();
      this.loadDepartments();
      this.initDoctorsActions();
    },

    // Patients Page
    init_patients() {
      this.loadPatientsList();
      this.initPatientsActions();
    },

    // Reports Page
    init_reports() {
      this.initReportsActions();
    },

    // Settings Page
    init_settings() {
      this.loadSettings();
      this.initSettingsActions();
    },

    async loadPatients() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_patients",
          args: { limit: 500 },
        });
        const result = this.apiResult(r);
        const patients = result.patients || [];
        
        const select = document.getElementById("hc-patient-select");
        if (select) {
          select.innerHTML = '<option value="">اختر المريض</option>';
          patients.forEach(patient => {
            const option = document.createElement("option");
            option.value = patient.name;
            option.textContent = `${patient.full_name || patient.name} (${patient.name})`;
            if (patient.mobile_no) {
              option.setAttribute("data-phone", patient.mobile_no);
            }
            select.appendChild(option);
          });

          select.onchange = (e) => {
            const selectedOption = select.options[select.selectedIndex];
            const phoneInput = document.getElementById("hc-patient-phone");
            if (phoneInput && selectedOption.getAttribute("data-phone")) {
              phoneInput.value = selectedOption.getAttribute("data-phone");
            }
          };
        }
      } catch (e) {
        console.error("Failed to load patients:", e);
      }
    },

    async loadPractitioners() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_practitioners",
          args: { limit: 500 },
        });
        const result = this.apiResult(r);
        const practitioners = result.practitioners || [];
        
        const selects = [
          document.getElementById("hc-practitioner-select"),
          document.getElementById("hc-filter-practitioner")
        ];
        
        selects.forEach(select => {
          if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">الكل</option>';
            practitioners.forEach(practitioner => {
              const option = document.createElement("option");
              option.value = practitioner.name;
              option.textContent = practitioner.practitioner_name;
              if (practitioner.specialty) {
                option.setAttribute("data-specialty", practitioner.specialty);
              }
              select.appendChild(option);
            });
            select.value = currentValue;
          }
        });
      } catch (e) {
        console.error("Failed to load practitioners:", e);
      }
    },

    async loadDepartments(selectIds = ["hc-department-select", "hc-filter-department"]) {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_departments",
        });
        const result = this.apiResult(r);
        const departments = result.departments || [];
        const placeholder = this.lang === "ar" ? "الكل" : "All";

        selectIds.forEach((selectId) => {
          const select = document.getElementById(selectId);
          if (!select) return;
          const isFilter = selectId.includes("filter");
          select.innerHTML = `<option value="">${isFilter ? placeholder : (this.lang === "ar" ? "اختر القسم" : "Select department")}</option>`;
          departments.forEach(dept => {
            const option = document.createElement("option");
            option.value = dept.name;
            option.textContent = dept.department_name || dept.name;
            select.appendChild(option);
          });
        });
      } catch (e) {
        console.error("Failed to load departments:", e);
      }
    },

    async loadSessions() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_sessions",
          args: { limit: 100 },
        });
        const result = this.apiResult(r);
        if (!result.success && result.error) {
          this.showError(result.error);
          return;
        }
        this.renderSessionsTable(result.sessions || []);
      } catch (e) {
        console.error("Failed to load sessions:", e);
        this.showError(this.lang === "ar" ? "تعذر تحميل الجلسات" : "Failed to load sessions");
      }
    },

    renderSessionsTable(sessions) {
      const tbody = document.getElementById("hc-sessions-tbody");
      if (!tbody) return;

      if (!sessions.length) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" class="hc-empty">
              <p id="hc-no-sessions">${this.lang === "ar" ? "لا توجد جلسات" : "No sessions"}</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = sessions.map(session => {
        const date = session.scheduled_datetime ? session.scheduled_datetime.split(" ")[0] : "-";
        const time = session.scheduled_datetime ? session.scheduled_datetime.split(" ")[1] || "-" : "-";
        const statusKey = (session.status || "scheduled").toLowerCase().replace(/\s+/g, "_");
        const statusClass = `hc-status-${statusKey}`;
        const statusText = this.getStatusText(session.status);

        return `
          <tr>
            <td>${session.name}</td>
            <td>${session.patient_name || session.patient || "-"}</td>
            <td>${session.practitioner_name || session.practitioner || "-"}</td>
            <td>${date}</td>
            <td>${time}</td>
            <td>${session.session_type || "-"}</td>
            <td><span class="hc-status-badge ${statusClass}">${statusText}</span></td>
            <td>
              <button class="hc-action-btn hc-btn-view" onclick="TelemedicineAdmin.viewSession('${session.name}')">عرض</button>
              <button class="hc-action-btn hc-btn-edit" onclick="TelemedicineAdmin.editSession('${session.name}')">تعديل</button>
              <button class="hc-action-btn hc-btn-delete" onclick="TelemedicineAdmin.deleteSession('${session.name}')">حذف</button>
            </td>
          </tr>
        `;
      }).join("");
    },

    showError(message) {
      if (typeof frappe !== "undefined" && frappe.msgprint) {
        frappe.msgprint({ message, indicator: "red" });
      } else {
        alert(message);
      }
    },

    getStatusText(status) {
      const key = (status || "").toLowerCase().replace(/\s+/g, "_");
      const statusMap = {
        scheduled: "مجدولة",
        in_progress: "قيد التنفيذ",
        completed: "مكتملة",
        cancelled: "ملغاة",
        no_show: "لم يحضر",
      };
      return statusMap[key] || status || "-";
    },

    initSessionsActions() {
      const filterBtn = document.getElementById("hc-filter-sessions");
      const newSessionBtn = document.getElementById("hc-new-session");
      const statusFilter = document.getElementById("hc-filter-status");
      const dateFilter = document.getElementById("hc-filter-date");
      const practitionerFilter = document.getElementById("hc-filter-practitioner");

      if (newSessionBtn) {
        newSessionBtn.addEventListener("click", () => {
          window.location.href = "/telemedicine-admin/sessions/new";
        });
      }

      if (filterBtn || statusFilter || dateFilter || practitionerFilter) {
        const applyFilters = () => {
          this.loadSessionsWithFilters();
        };

        if (filterBtn) filterBtn.addEventListener("click", applyFilters);
        if (statusFilter) statusFilter.addEventListener("change", applyFilters);
        if (dateFilter) dateFilter.addEventListener("change", applyFilters);
        if (practitionerFilter) practitionerFilter.addEventListener("change", applyFilters);
      }
    },

    async loadSessionsWithFilters() {
      const status = document.getElementById("hc-filter-status")?.value;
      const date = document.getElementById("hc-filter-date")?.value;
      const practitioner = document.getElementById("hc-filter-practitioner")?.value;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_sessions",
          args: { status, date, practitioner, limit: 100 },
        });
        const result = this.apiResult(r);
        if (!result.success && result.error) {
          this.showError(result.error);
          return;
        }
        this.renderSessionsTable(result.sessions || []);
      } catch (e) {
        console.error("Failed to load sessions with filters:", e);
        this.showError(this.lang === "ar" ? "تعذر تصفية الجلسات" : "Failed to filter sessions");
      }
    },

    initNewSessionActions() {
      const cancelBtn = document.getElementById("hc-cancel-session");
      const createBtn = document.getElementById("hc-create-session");

      if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
          window.location.href = "/telemedicine-admin/sessions";
        });
      }

      if (createBtn) {
        createBtn.addEventListener("click", () => {
          this.createNewSession();
        });
      }
    },

    async createNewSession() {
      const patient = document.getElementById("hc-patient-select")?.value;
      const practitioner = document.getElementById("hc-practitioner-select")?.value;
      const department = document.getElementById("hc-department-select")?.value;
      const date = document.getElementById("hc-session-date")?.value;
      const time = document.getElementById("hc-session-time")?.value;
      const duration = document.getElementById("hc-session-duration")?.value;
      const consultationType = document.getElementById("hc-consultation-type")?.value;
      const appointmentType = document.getElementById("hc-appointment-type")?.value;
      const notes = document.getElementById("hc-session-notes")?.value;
      const consent = document.getElementById("hc-consent-check")?.checked;

      if (!patient || !practitioner || !date || !time || !consultationType) {
        alert("يرجى ملء جميع الحقول المطلوبة");
        return;
      }

      if (!consent) {
        alert("يجب الموافقة على شروط وأحكام الطب عن بعد");
        return;
      }

      const typeMap = {
        video: "Video",
        voice: "Voice",
        chat: "Chat",
      };

      try {
        const scheduled_datetime = `${date} ${time}:00`;

        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.create_admin_session",
          args: {
            data: {
              patient,
              practitioner,
              date,
              time: scheduled_datetime.split(" ")[1],
              session_type: typeMap[consultationType] || consultationType,
              notes,
            },
          },
        });

        const result = this.apiResult(r);
        if (result.success) {
          alert(this.lang === "ar" ? "تم إنشاء الجلسة بنجاح" : "Session created successfully");
          window.location.href = "/telemedicine-admin/sessions";
        } else {
          alert(result.error || (this.lang === "ar" ? "حدث خطأ أثناء إنشاء الجلسة" : "Failed to create session"));
        }
      } catch (e) {
        console.error("Failed to create session:", e);
        alert(this.lang === "ar" ? "حدث خطأ أثناء إنشاء الجلسة" : "Failed to create session");
      }
    },

    viewSession(name) {
      window.location.href = `/app/healthcare-telemedicine-session/${name}`;
    },

    editSession(name) {
      window.location.href = `/app/healthcare-telemedicine-session/${name}`;
    },

    async deleteSession(name) {
      if (!confirm("هل أنت متأكد من حذف هذه الجلسة؟")) {
        return;
      }

      try {
        await frappe.call({
          method: "frappe.client.delete",
          args: {
            doctype: "Healthcare Telemedicine Session",
            name: name,
          },
        });
        
        alert("تم حذف الجلسة بنجاح");
        this.loadSessions();
      } catch (e) {
        console.error("Failed to delete session:", e);
        alert("حدث خطأ أثناء حذف الجلسة");
      }
    },

    async loadDoctors() {
      const tbody = document.getElementById("hc-doctors-tbody");
      if (!tbody) return;

      const department = document.getElementById("hc-filter-department")?.value || "";
      const status = document.getElementById("hc-filter-status")?.value || "";

      try {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="hc-empty">
              <p>${this.lang === "ar" ? "جاري التحميل..." : "Loading..."}</p>
            </td>
          </tr>
        `;

        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_doctors",
          args: { department, status, limit: 100 },
        });
        const result = this.apiResult(r);
        const doctors = result.doctors || [];

        if (!result.success && result.error) {
          this.showError(result.error);
          return;
        }

        if (!doctors.length) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="hc-empty">
                <p id="hc-no-doctors">${this.lang === "ar" ? "لا يوجد أطباء" : "No doctors found"}</p>
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = doctors.map(doctor => `
          <tr>
            <td>${doctor.practitioner_name || "-"}</td>
            <td>${doctor.department || doctor.specialty || "-"}</td>
            <td>${doctor.company || "-"}</td>
            <td><span class="hc-status-badge hc-status-${doctor.status === "Active" ? "success" : "warning"}">${doctor.status === "Active" ? "نشط" : "غير نشط"}</span></td>
            <td>
              <button class="hc-action-btn hc-btn-view" onclick="TelemedicineAdmin.viewDoctor('${doctor.name}')">عرض</button>
            </td>
          </tr>
        `).join("");
      } catch (e) {
        console.error("Failed to load doctors:", e);
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="hc-empty">
              <p>${this.lang === "ar" ? "تعذر تحميل الأطباء" : "Failed to load doctors"}</p>
            </td>
          </tr>
        `;
      }
    },

    viewDoctor(name) {
      window.location.href = `/app/healthcare-practitioner/${name}`;
    },

    initDoctorsActions() {
      const viewBtn = document.getElementById("hc-view-practitioners");
      const filterBtn = document.getElementById("hc-filter-doctors");
      const departmentFilter = document.getElementById("hc-filter-department");
      const statusFilter = document.getElementById("hc-filter-status");

      if (viewBtn) {
        viewBtn.addEventListener("click", () => {
          window.location.href = "/app/healthcare-practitioner/view/list";
        });
      }

      const applyFilters = () => this.loadDoctors();
      if (departmentFilter) departmentFilter.addEventListener("change", applyFilters);
      if (statusFilter) statusFilter.addEventListener("change", applyFilters);
      if (filterBtn) filterBtn.addEventListener("click", applyFilters);
    },

    async loadPatientsList() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_admin_patients",
          args: { limit: 100 },
        });
        const result = this.apiResult(r);
        const patients = result.patients || [];
        
        const tbody = document.getElementById("hc-patients-tbody");
        if (!tbody) return;

        if (!patients.length) {
          tbody.innerHTML = `
            <tr>
              <td colspan="3" class="hc-empty">
                <p id="hc-no-patients">${this.lang === "ar" ? "لا يوجد مرضى" : "No patients found"}</p>
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = patients.map(patient => `
          <tr>
            <td>${patient.full_name || patient.name || "-"}</td>
            <td><span class="hc-status-badge hc-status-${patient.active ? "success" : "warning"}">${patient.active ? "نشط" : "غير نشط"}</span></td>
            <td>
              <button class="hc-action-btn hc-btn-view" onclick="TelemedicineAdmin.viewPatient('${patient.name}')">عرض</button>
            </td>
          </tr>
        `).join("");
      } catch (e) {
        console.error("Failed to load patients:", e);
      }
    },

    viewPatient(name) {
      window.location.href = `/app/healthcare-patient/${name}`;
    },

    initPatientsActions() {
      const viewBtn = document.getElementById("hc-view-patients");
      if (viewBtn) {
        viewBtn.addEventListener("click", () => {
          window.location.href = "/app/healthcare-patient/view/list";
        });
      }
    },

    initReportsActions() {
      const generateBtn = document.getElementById("hc-generate-report");
      const exportBtn = document.getElementById("hc-export-report");

      if (generateBtn) {
        generateBtn.addEventListener("click", () => this.generateReport());
      }

      if (exportBtn) {
        exportBtn.addEventListener("click", () => this.exportReport());
      }
    },

    async generateReport() {
      const reportType = document.getElementById("hc-report-type")?.value || "sessions";
      const fromDate = document.getElementById("hc-from-date")?.value;
      const toDate = document.getElementById("hc-to-date")?.value;
      const filters = {};
      if (fromDate) filters.from_date = fromDate;
      if (toDate) filters.to_date = toDate;

      const methodMap = {
        sessions: "omnexa_healthcare.api.telemedicine_admin.get_session_stats",
        revenue: "omnexa_healthcare.api.telemedicine_admin.get_revenue_report",
        usage: "omnexa_healthcare.api.telemedicine_admin.get_usage_report",
      };

      try {
        const r = await frappe.call({
          method: methodMap[reportType] || methodMap.sessions,
          args: { filters },
        });
        const result = this.apiResult(r);
        const stats = result.stats || result.report || {};
        document.getElementById("hc-total-sessions").textContent = stats.total_sessions || stats.by_status?.scheduled || 0;
        document.getElementById("hc-completed-sessions").textContent = stats.completed || stats.completed_sessions || stats.by_status?.completed || 0;
        document.getElementById("hc-avg-rating").textContent = Number(stats.average_rating || 0).toFixed(1);
        document.getElementById("hc-total-revenue").textContent = Number(stats.total_revenue || 0).toLocaleString();

        const placeholder = document.getElementById("hc-chart-placeholder");
        if (placeholder) {
          placeholder.innerHTML = this.renderReportSummary(stats, reportType);
        }
      } catch (e) {
        console.error("Failed to generate report:", e);
        alert("حدث خطأ أثناء إنشاء التقرير");
      }
    },

    exportReport() {
      const placeholder = document.getElementById("hc-chart-placeholder");
      if (!placeholder || !placeholder.innerHTML.trim()) {
        alert("قم بإنشاء التقرير أولاً");
        return;
      }
      const blob = new Blob([placeholder.innerText], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "telemedicine-report.json";
      link.click();
      URL.revokeObjectURL(url);
    },

    renderReportSummary(stats, reportType) {
      const rows = [];
      if (reportType === "revenue") {
        rows.push(["Total Revenue", stats.total_revenue || 0]);
        rows.push(["Completed Charges", stats.completed_charges || 0]);
      } else if (reportType === "usage") {
        Object.entries(stats.by_type || {}).forEach(([key, val]) => rows.push([key, val]));
      } else {
        rows.push(["Total Sessions", stats.total_sessions || 0]);
        rows.push(["Completed", stats.completed || stats.completed_sessions || 0]);
        rows.push(["In Progress", stats.in_progress || 0]);
        rows.push(["Average Rating", stats.average_rating || 0]);
      }
      return `
        <table class="hc-table">
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>
            ${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("")}
          </tbody>
        </table>
      `;
    },

    async loadSettings() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_config",
        });
        
        if (r.message && r.message.config) {
          const config = r.message.config;
          
          // General settings
          document.getElementById("hc-enable-video").checked = config.enable_video_consultations || false;
          document.getElementById("hc-enable-voice").checked = config.enable_voice_consultations || false;
          document.getElementById("hc-enable-chat").checked = config.enable_chat_consultations || false;
          document.getElementById("hc-default-duration").value = config.default_session_duration || 30;
          document.getElementById("hc-max-duration").value = config.max_session_duration || 60;
          document.getElementById("hc-max-concurrent").value = config.max_concurrent_sessions || 100;
          document.getElementById("hc-session-timeout").value = config.session_timeout_minutes || 15;
          
          // Video settings
          document.getElementById("hc-jitsi-domain").value = config.jitsi_domain || "meet.jit.si";
          document.getElementById("hc-jitsi-app-id").value = config.jitsi_app_id || "";
          document.getElementById("hc-jitsi-secret").value = config.jitsi_secret || "";
          document.getElementById("hc-turn-url").value = config.turn_server_url || "";
          document.getElementById("hc-stun-url").value = config.stun_server_url || "stun:stun.l.google.com:19302";
          document.getElementById("hc-video-quality").value = config.video_quality || "HD";
          
          // Features settings
          document.getElementById("hc-enable-screen-share").checked = config.enable_screen_sharing || false;
          document.getElementById("hc-enable-whiteboard").checked = config.enable_whiteboard || false;
          document.getElementById("hc-enable-file-share").checked = config.enable_file_sharing || false;
          document.getElementById("hc-max-file-size").value = config.max_file_size_mb || 10;
          document.getElementById("hc-allowed-file-types").value = config.allowed_file_types || "pdf,jpg,jpeg,png,doc,docx";
          document.getElementById("hc-enable-recording").checked = config.allow_recording || false;
          document.getElementById("hc-auto-record").checked = config.auto_record || false;
          
          // AI settings
          document.getElementById("hc-enable-transcription").checked = config.enable_ai_transcription || false;
          document.getElementById("hc-enable-summarization").checked = config.enable_ai_summarization || false;
        }
      } catch (e) {
        console.error("Failed to load settings:", e);
      }
    },

    initSettingsActions() {
      // Tab switching
      const tabBtns = document.querySelectorAll(".hc-tab-btn");
      tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
          const tab = btn.getAttribute("data-tab");
          
          // Remove active class from all tabs and panels
          tabBtns.forEach(b => b.classList.remove("active"));
          document.querySelectorAll(".hc-settings-panel").forEach(p => p.classList.remove("active"));
          
          // Add active class to clicked tab and corresponding panel
          btn.classList.add("active");
          document.getElementById(`hc-panel-${tab}`).classList.add("active");
        });
      });

      // Save settings
      const saveBtn = document.getElementById("hc-save-settings");
      if (saveBtn) {
        saveBtn.addEventListener("click", () => {
          this.saveSettings();
        });
      }

      // Reset settings
      const resetBtn = document.getElementById("hc-reset-settings");
      if (resetBtn) {
        resetBtn.addEventListener("click", () => {
          if (confirm("هل أنت متأكد من إعادة تعيين الإعدادات؟")) {
            this.loadSettings();
          }
        });
      }
    },

    async saveSettings() {
      const settings = {
        enable_video_consultations: document.getElementById("hc-enable-video").checked,
        enable_voice_consultations: document.getElementById("hc-enable-voice").checked,
        enable_chat_consultations: document.getElementById("hc-enable-chat").checked,
        default_session_duration: parseInt(document.getElementById("hc-default-duration").value),
        max_session_duration: parseInt(document.getElementById("hc-max-duration").value),
        max_concurrent_sessions: parseInt(document.getElementById("hc-max-concurrent").value),
        session_timeout_minutes: parseInt(document.getElementById("hc-session-timeout").value),
        jitsi_domain: document.getElementById("hc-jitsi-domain").value,
        jitsi_app_id: document.getElementById("hc-jitsi-app-id").value,
        jitsi_secret: document.getElementById("hc-jitsi-secret").value,
        turn_server_url: document.getElementById("hc-turn-url").value,
        stun_server_url: document.getElementById("hc-stun-url").value,
        video_quality: document.getElementById("hc-video-quality").value,
        enable_screen_sharing: document.getElementById("hc-enable-screen-share").checked,
        enable_whiteboard: document.getElementById("hc-enable-whiteboard").checked,
        enable_file_sharing: document.getElementById("hc-enable-file-share").checked,
        max_file_size_mb: parseInt(document.getElementById("hc-max-file-size").value),
        allowed_file_types: document.getElementById("hc-allowed-file-types").value,
        allow_recording: document.getElementById("hc-enable-recording").checked,
        auto_record: document.getElementById("hc-auto-record").checked,
        enable_ai_transcription: document.getElementById("hc-enable-transcription").checked,
        enable_ai_summarization: document.getElementById("hc-enable-summarization").checked,
      };

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.update_config",
          args: {
            data: settings,
          },
        });

        if (r.message && r.message.success) {
          alert("تم حفظ الإعدادات بنجاح");
        } else {
          alert("حدث خطأ أثناء حفظ الإعدادات");
        }
      } catch (e) {
        console.error("Failed to save settings:", e);
        alert("حدث خطأ أثناء حفظ الإعدادات");
      }
    },

    async loadStats() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_dashboard_stats",
        });
        const result = this.apiResult(r);
        if (result.success) {
          this.stats = result.stats || {};
          this.updateStatUI();
        }
      } catch (e) {
        console.error("Failed to load stats:", e);
        this.stats = {
          active_sessions: 0,
          today_sessions: 0,
          satisfaction: 0,
          revenue: 0,
          issues: 0,
          active_doctors: 0,
        };
        this.updateStatUI();
      }
    },

    updateStatUI() {
      const elements = {
        "hc-active-sessions": this.stats.active_sessions,
        "hc-today-sessions": this.stats.today_sessions,
        "hc-satisfaction": Number(this.stats.satisfaction || 0).toFixed(1),
        "hc-revenue": Number(this.stats.revenue || 0).toLocaleString(),
        "hc-issues": this.stats.issues,
        "hc-active-doctors": this.stats.active_doctors,
      };

      for (const [id, value] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
      }
    },

    async loadLiveSessions() {
      const list = document.getElementById("hc-sessions-list");
      if (!list) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_active_sessions",
        });
        const result = this.apiResult(r);
        const sessions = result.sessions || [];

        if (!sessions.length) {
          list.innerHTML = `<div class="hc-empty"><p>${this.t("no_sessions")}</p></div>`;
          return;
        }

        list.innerHTML = sessions.map((s) => `
          <div class="hc-session-item">
            <div class="hc-session-avatar">👤</div>
            <div class="hc-session-info">
              <div class="hc-session-name">${s.patient_display || s.patient || "-"}</div>
              <div class="hc-session-meta">
                <span>${s.practitioner_display || s.practitioner || "-"}</span>
                <span>•</span>
                <span class="hc-session-duration">${s.session_type || "-"}</span>
              </div>
            </div>
            <div class="hc-session-status hc-status-active">
              ${this.t("active_sessions")}
            </div>
          </div>
        `).join("");
      } catch (e) {
        console.error("Failed to load live sessions:", e);
      }
    },

    async loadSystemHealth() {
      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_system_health",
        });
        const result = this.apiResult(r);
        const health = result.health || {};

        const elements = {
          "hc-server-status": health.video_server || "not_configured",
          "hc-turn-status": health.turn_server || "not_configured",
          "hc-db-status": health.database || "error",
          "hc-redis-status": health.redis || "not_configured",
          "hc-storage-status": health.storage || "ok",
        };

        for (const [id, value] of Object.entries(elements)) {
          const el = document.getElementById(id);
          if (el) {
            el.textContent = value === "connected" ? this.t("connected") : value;
            el.className = "hc-health-status hc-status-" + (value === "connected" ? "connected" : value);
          }
        }
      } catch (e) {
        console.error("Failed to load system health:", e);
      }
    },

    async loadAlerts() {
      const list = document.getElementById("hc-alerts-list");
      const count = document.getElementById("hc-alert-count");
      if (!list) return;

      try {
        const r = await frappe.call({
          method: "omnexa_healthcare.api.telemedicine_admin.get_alerts",
        });
        const result = this.apiResult(r);
        const alerts = result.alerts || [];

        if (count) count.textContent = alerts.length;

        if (!alerts.length) {
          list.innerHTML = `<div class="hc-empty"><p>${this.t("no_alerts")}</p></div>`;
          return;
        }

        list.innerHTML = alerts.map((a) => `
          <div class="hc-alert-item ${a.type}">
            <div class="hc-alert-icon">
              ${a.type === "critical" ? "🚨" : a.type === "warning" ? "⚠️" : "ℹ️"}
            </div>
            <div class="hc-alert-content">
              <div class="hc-alert-text">${a.text}</div>
              <div class="hc-alert-time">${a.time || ""}</div>
            </div>
          </div>
        `).join("");
      } catch (e) {
        console.error("Failed to load alerts:", e);
      }
    },

    initActions() {
      const refreshBtn = document.getElementById("hc-refresh-dashboard");
      const newSessionBtn = document.getElementById("hc-new-session");

      if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
          this.loadStats();
          this.loadLiveSessions();
          this.loadSystemHealth();
          this.loadAlerts();
        });
      }

      if (newSessionBtn) {
        newSessionBtn.addEventListener("click", () => {
          window.location.href = "/telemedicine-admin/sessions/new";
        });
      }

      // Quick actions
      const quickActions = {
        "hc-manage-doctors": "/telemedicine-admin/doctors",
        "hc-manage-patients": "/telemedicine-admin/patients",
        "hc-view-reports": "/telemedicine-admin/reports",
        "hc-system-settings": "/telemedicine-admin/settings",
      };

      for (const [id, href] of Object.entries(quickActions)) {
        const btn = document.getElementById(id);
        if (btn) {
          btn.addEventListener("click", () => {
            window.location.href = href;
          });
        }
      }
    },
  };
})();
