/**
 * Omnexa Journey Kit — extends OmnexaJourney with desk helpers, ERP embed, portals
 */
/* global frappe, omnexa_core */
(function (window) {
	"use strict";
	const OJ = window.OmnexaJourney;
	if (!OJ) return;

	const origShell = OJ.shell;

	function navigateRoute(route) {
		if (!route || route === "#") return;
		if (route.startsWith("/app/")) {
			window.location.href = route;
			return;
		}
		if (route.startsWith("List/")) {
			frappe.set_route("List", route.slice(5));
			return;
		}
		if (route.startsWith("Form/")) {
			const parts = route.split("/");
			frappe.set_route("Form", parts[1], parts[2] || "");
			return;
		}
		frappe.set_route(route);
	}

	function resolveCompanyBranch() {
		return {
			company: frappe.defaults.get_user_default("Company") || "",
			branch: frappe.defaults.get_user_default("Branch") || "",
		};
	}

	function showCallError(err, fallback) {
		const msg = (err && (err.message || err._error_message)) || fallback || OJ.t("تعذر التحميل", "Could not load data");
		frappe.msgprint({ title: OJ.t("خطأ", "Error"), indicator: "red", message: msg });
	}

	function dataTable(columns, rows) {
		const cols = columns || [];
		const head = cols.map((c) => `<th>${OJ.esc(c.label)}</th>`).join("");
		const body = (rows || [])
			.map((row) => {
				const cells = cols.map((c) => `<td>${OJ.esc(row[c.field] ?? "—")}</td>`).join("");
				return `<tr>${cells}</tr>`;
			})
			.join("");
		return `<div class="oj-table-wrap"><table class="oj-data-table"><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${cols.length || 1}" class="oj-muted">${OJ.t("لا بيانات", "No data")}</td></tr>`}</tbody></table></div>`;
	}

	function linkGrid(links) {
		const $g = $('<div class="oj-link-grid"></div>');
		(links || []).forEach((link) => {
			const $card = $(`<div class="oj-link-card"><div class="oj-link-icon">${link.icon || "•"}</div><div class="oj-link-label">${OJ.esc(link.label)}</div></div>`);
			$card.on("click", () => navigateRoute(link.route));
			$g.append($card);
		});
		return $g;
	}

	function portalCategoryGrid(groups) {
		const $root = $('<div class="oj-portal-catalog oj-demo-portals"></div>');
		(groups || []).forEach((g) => {
			const title = OJ.lang() === "ar" ? g.label_ar : g.label_en;
			const $sec = $(`<div class="oj-portal-section"><h4 class="oj-portal-cat-title">${OJ.esc(title)}</h4></div>`);
			const clinics = (g.portals || []).map((p) => ({
				id: p.id,
				name: OJ.lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: OJ.t("بوابة خارجية", "Outpatient portal"),
				icon: p.icon || "🏥",
				doctor_count: (p.roles || []).length,
				waiting_count: 0,
				route: p.route,
				_disabled: p.exists === false,
			}));
			if (OJ.clinicGrid) {
				const $grid = OJ.clinicGrid(
					clinics.filter((c) => !c._disabled),
					(c) => navigateRoute(c.route)
				);
				$sec.append($grid);
				clinics
					.filter((c) => c._disabled)
					.forEach((c) => {
						const $card = $(`
							<div class="oj-clinic-card oj-muted-card" style="margin-top:8px">
								<div class="oj-clinic-icon">${c.icon || "🏥"}</div>
								<h4>${OJ.esc(c.name)}</h4>
								<p class="oj-muted">${OJ.esc(c.subtitle)}</p>
								<div class="oj-clinic-stats"><span>👤 ${OJ.t("غير متاح", "Unavailable")}</span></div>
							</div>
						`);
						$sec.append($card);
					});
			} else {
				const $grid = $('<div class="oj-clinic-grid"></div>');
				clinics.forEach((c) => {
					const $card = $(`
						<div class="oj-clinic-card ${c._disabled ? "oj-muted-card" : ""}">
							<div class="oj-clinic-icon">${c.icon || "🏥"}</div>
							<h4>${OJ.esc(c.name)}</h4>
							<p class="oj-muted">${OJ.esc(c.subtitle)}</p>
							<div class="oj-clinic-stats">
								<span>👤 ${OJ.esc(String(c.doctor_count))} ${OJ.t("أدوار", "roles")}</span>
							</div>
							<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${OJ.t("اختيار", "Select")}</button>
						</div>
					`);
					if (!c._disabled) $card.on("click", () => navigateRoute(c.route));
					$grid.append($card);
				});
				$sec.append($grid);
			}
			$root.append($sec);
		});
		return $root;
	}

	function bindSidebarNav($root, homeRoute) {
		$root.find(".oj-sidebar-item[data-nav-route]").on("click", function (e) {
			e.preventDefault();
			navigateRoute($(this).attr("data-nav-route"));
		});
		if (homeRoute) {
			$root.find("[data-oj-home]").on("click", function (e) {
				e.preventDefault();
				navigateRoute(homeRoute);
			});
		}
	}

	function currentLang() {
		return OJ.lang();
	}

	function switchLanguage(langCode) {
		if (!langCode || langCode === currentLang()) return;
		frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "User",
				name: frappe.session.user,
				fieldname: "language",
				value: langCode,
			},
			callback() {
				window.location.reload();
			},
		});
	}

	function userMenuHtml() {
		const name = frappe.session.user_fullname || frappe.session.user;
		return `<div class="oj-user-menu">
			<button type="button" class="oj-user-btn" aria-haspopup="true" aria-expanded="false">
				<span class="oj-user-avatar">${OJ.esc((name || "U").charAt(0).toUpperCase())}</span>
				<span class="oj-user-name">${OJ.esc(name)}</span>
				<span class="oj-user-caret">▾</span>
			</button>
			<div class="oj-user-dropdown" role="menu">
				<div class="oj-user-dropdown-title">${OJ.t("الحساب", "Account")}</div>
				<a href="/app/user-profile" class="oj-user-dropdown-item" role="menuitem">⚙ ${OJ.t("الملف الشخصي", "Profile")}</a>
			</div>
		</div>`;
	}

	function bindUserMenu($root) {
		const $menu = $root.find(".oj-user-menu");
		$menu.find(".oj-user-btn").on("click", function (e) {
			e.stopPropagation();
			$menu.toggleClass("open");
			$(this).attr("aria-expanded", $menu.hasClass("open"));
		});
		$(document).on("click.ojUserMenu", () => $menu.removeClass("open"));
	}

	function patientSearchBar(options) {
		const placeholder =
			(options && options.placeholder) ||
			OJ.t("الاسم / الرقم القومي / الجوال / MRN", "Name / National ID / Mobile / MRN");
		return `<div class="oj-search-bar oj-patient-search-bar">
			<input type="text" class="oj-patient-query oj-patient-search" placeholder="${OJ.esc(placeholder)}" />
			<button type="button" class="oj-btn oj-btn-primary oj-patient-search-btn oj-search-btn">${OJ.t("بحث", "Search")}</button>
		</div>
		<div class="oj-patient-search-results oj-patient-results"></div>`;
	}

	function bindPatientSearch($root, onSelect, branch, company) {
		const run = async () => {
			const query = ($root.find(".oj-patient-query, .oj-patient-search").val() || "").trim();
			const $results = $root.find(".oj-patient-search-results, .oj-patient-results").first();
			$results.html(OJ.loading());
			if (!query || query.length < 2) {
				$results.html(`<p class="oj-muted">${OJ.t("أدخل حرفين على الأقل", "Enter at least 2 characters")}</p>`);
				return;
			}
			try {
				const rows = await OJ.call("omnexa_healthcare.api.journey_desk.search_patient_quick", {
					query,
					branch: branch || frappe.defaults.get_user_default("Branch"),
					company: company || frappe.defaults.get_user_default("Company"),
				});
				if (!rows.length) {
					$results.html(
						`<p class="oj-muted">${OJ.t("لا نتائج — جرّب الاسم أو الرقم القومي أو الجوال", "No results — try name, national ID, or mobile")}</p>`
					);
					return;
				}
				const matchLabel = (type) => {
					const map = {
						Name: OJ.t("الاسم", "Name"),
						Mobile: OJ.t("الجوال", "Mobile"),
						Phone: OJ.t("الهاتف", "Phone"),
						"National ID": OJ.t("الرقم القومي", "National ID"),
						MRN: OJ.t("MRN", "MRN"),
					};
					return map[type] || type;
				};
				const $list = $('<div class="oj-patient-search-list"></div>');
				rows.forEach((r) => {
					const patientId = r.patient || r.name;
					const display = r.patient_name || r.full_name || r.patient_display || patientId;
					const $btn = $(`<button type="button" class="oj-btn oj-btn-outline oj-patient-pick" style="margin:4px;width:100%;text-align:start">
						<strong>${OJ.esc(display)}</strong>
						<span class="oj-muted"> · ${OJ.esc(matchLabel(r.match_type))}: ${OJ.esc(r.match_value || "")}</span>
						<span class="oj-muted"> · ${OJ.esc(r.branch || "")}</span>
					</button>`);
					$btn.on("click", () => onSelect && onSelect({ ...r, name: patientId, patient: patientId }));
					$list.append($btn);
				});
				$results.empty().append($list);
			} catch (err) {
				$results.html(`<p class="oj-muted">${OJ.t("تعذر البحث", "Search failed")}</p>`);
				OJ.showCallError(err);
			}
		};
		$root.find(".oj-patient-search-btn, .oj-search-btn").off("click.ojPatientSearch").on("click.ojPatientSearch", run);
		$root.find(".oj-patient-query, .oj-patient-search").off("keydown.ojPatientSearch").on("keydown.ojPatientSearch", (e) => {
			if (e.key === "Enter") {
				e.preventDefault();
				run();
			}
		});
	}

	function alertList(alerts) {
		const items = (alerts || [])
			.map((a) => `<li class="oj-alert oj-alert-${OJ.esc(a.level || "info")}">${OJ.esc(a.text || "")}</li>`)
			.join("");
		if (!items) return `<p class="oj-muted">${OJ.t("لا تنبيهات", "No alerts")}</p>`;
		return `<ul class="oj-alert-list">${items}</ul>`;
	}

	OJ.shell = function (options) {
		const opts = options || {};
		const sidebar = (opts.sidebar || []).map((n) => ({
			...n,
			route: n.route,
		}));
		const navHtml = sidebar
			.map(
				(n) =>
					`<a class="oj-sidebar-item ${n.active ? "active" : ""}" href="#" data-nav-route="${OJ.esc(n.route || "")}"><span class="oj-sidebar-icon">${n.icon || "•"}</span><span>${OJ.esc(n.label)}</span></a>`
			)
			.join("");
		const isRtl = OJ.lang() === "ar";
		const $root = $(`<div class="oj-shell oj-desk-page ${isRtl ? "oj-rtl" : "oj-ltr"}" dir="${isRtl ? "rtl" : "ltr"}"></div>`);
		const kpiHtml = (opts.kpis || [])
			.map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${OJ.esc(k.value)}</div><div class="oj-kpi-label">${OJ.esc(k.label)}</div></div>`)
			.join("");
		$root.html(`
			<aside class="oj-sidebar">${navHtml}<div class="oj-sidebar-spacer"></div>
				<a class="oj-sidebar-item" href="#" data-oj-home="1">🏠 ${OJ.t("الرئيسية", "Home")}</a>
				<a class="oj-sidebar-item oj-logout" href="/app">⏻ ${OJ.t("خروج", "Logout")}</a>
			</aside>
			<div class="oj-main">
				<header class="oj-topbar"><div class="oj-topbar-brand"><span class="oj-logo">+</span><div><strong>Omnexa Healthcare</strong><small>${OJ.esc(opts.subtitle || "")}</small></div></div>
				<div class="oj-topbar-meta"><span class="oj-pill">${OJ.esc(opts.role || "")}</span>${userMenuHtml()}</div></header>
				<div class="oj-title-row"><h1>${OJ.esc(opts.title || "")}</h1></div>
				${kpiHtml ? `<div class="oj-kpi-row">${kpiHtml}</div>` : ""}
				<div class="oj-body"></div>
			</div>`);
		const $body = $root.find(".oj-body");
		if (opts.bodyEl) $body.append(opts.bodyEl);
		else if (opts.body) $body.html(opts.body);
		bindSidebarNav($root, opts.homeRoute);
		bindUserMenu($root);
		return $root;
	};

	function loadRetailPosAssets() {
		return new Promise((resolve) => {
			frappe.require(
				[
					"/assets/omnexa_core/css/retail_pos.css",
					"/assets/omnexa_core/css/retail_product_manager.css",
					"/assets/omnexa_core/js/retail_product_manager.js",
					"/assets/omnexa_core/js/retail_pos.js",
				],
				resolve
			);
		});
	}

	async function embedRetailPos(container, options) {
		await loadRetailPosAssets();
		const $host = $(container).addClass("oj-retail-pos-host").empty();
		const pos = omnexa_core.retail_pos.init($host[0], Object.assign({ embedded: true, hideSidebar: true }, options || {}));
		return pos || omnexa_core.retail_pos;
	}

	async function wrapLegacyDesk(wrapper, opts) {
		const $mount = OJ.mountDeskPage(wrapper, opts.deskTitle || opts.title);
		const $body = $('<div class="oj-legacy-wrap"></div>');
		if (opts.render) await opts.render($body);
		const $shell = OJ.shell({
			title: opts.title,
			subtitle: opts.subtitle || OJ.t("Omnexa Healthcare", "Omnexa Healthcare"),
			role: opts.role || "",
			kpis: opts.kpis,
			sidebar: opts.sidebar || OJ.defaultSidebar(opts.sidebarRole || "reception"),
			bodyEl: $body,
			homeRoute: opts.homeRoute,
		});
		$mount.empty().append($shell);
		return { $mount, $body, $shell };
	}

	function defaultSidebar(role) {
		const menus = {
			reception: [
				{ id: "home", label: OJ.t("الاستقبال", "Reception"), icon: "🏥", route: "/app/healthcare-reception-desk", active: true },
				{ id: "queue", label: OJ.t("الانتظار", "Queue"), icon: "📋", route: "/app/healthcare-patient-queue" },
				{ id: "appts", label: OJ.t("المواعيد", "Appointments"), icon: "📅", route: "/app/healthcare-appointments-desk" },
			],
			pharmacy: [
				{ id: "home", label: OJ.t("الصيدلية", "Pharmacy"), icon: "💊", route: "/app/healthcare-pharmacy-desk", active: true },
				{ id: "rx", label: OJ.t("الروشتات", "Rx"), icon: "📝", route: "List/Healthcare Medication Statement" },
			],
			finance: [
				{ id: "home", label: OJ.t("المالية", "Finance"), icon: "💼", route: "/app/healthcare-finance-desk", active: true },
				{ id: "cashier", label: OJ.t("الخزينة", "Cashier"), icon: "💰", route: "/app/healthcare-cashier-desk" },
			],
			manager: [
				{ id: "home", label: OJ.t("المدير", "Manager"), icon: "📊", route: "/app/healthcare-executive-dashboard", active: true },
				{ id: "demo", label: OJ.t("مركز الديمو", "Demo Hub"), icon: "🎯", route: "/app/healthcare-demo-hub" },
			],
			nurse: [
				{ id: "home", label: OJ.t("التمريض", "Nursing"), icon: "🩹", route: "/app/healthcare-nursing-portal", active: true },
				{ id: "queue", label: OJ.t("الانتظار", "Queue"), icon: "📋", route: "/app/healthcare-patient-queue" },
				{ id: "icu", label: OJ.t("ICU", "ICU"), icon: "🏥", route: "/app/healthcare-icu-board" },
			],
			lab: [
				{ id: "home", label: OJ.t("المعمل", "Laboratory"), icon: "🔬", route: "/app/healthcare-lab-workbench", active: true },
				{ id: "samples", label: OJ.t("العينات", "Samples"), icon: "🧪", route: "List/Healthcare Lab Sample" },
				{ id: "reports", label: OJ.t("النتائج", "Results"), icon: "📄", route: "List/Healthcare Diagnostic Report" },
				{ id: "devices", label: OJ.t("الأجهزة", "Devices"), icon: "🔌", route: "/app/healthcare-device-admin" },
			],
			radiology: [
				{ id: "home", label: OJ.t("الأشعة", "Radiology"), icon: "🩻", route: "/app/healthcare-radiology-worklist", active: true },
				{ id: "orders", label: OJ.t("الطلبات", "Orders"), icon: "📋", route: "List/Healthcare Service Request" },
				{ id: "dicom", label: OJ.t("عارض DICOM", "DICOM Viewer"), icon: "🖼", route: "/app/healthcare-dicom-viewer" },
				{ id: "devices", label: OJ.t("الأجهزة", "Devices"), icon: "🔌", route: "/app/healthcare-device-admin" },
			],
			dental: [
				{ id: "home", label: OJ.t("عيادة الأسنان", "Dental Clinic"), icon: "🦷", route: "/app/healthcare-dental-chart", active: true },
				{ id: "plans", label: OJ.t("خطط العلاج", "Treatment Plans"), icon: "📋", route: "List/Healthcare Dental Treatment Plan" },
				{ id: "appts", label: OJ.t("المواعيد", "Appointments"), icon: "📅", route: "/app/healthcare-appointments-desk" },
			],
			admin: [
				{ id: "demo", label: OJ.t("مركز الديمو", "Demo Hub"), icon: "🎯", route: "/app/healthcare-demo-hub", active: true },
				{ id: "devices", label: OJ.t("الأجهزة", "Devices"), icon: "🔌", route: "/app/healthcare-device-admin" },
			],
		};
		return menus[role] || menus.reception;
	}

	Object.assign(OJ, {
		navigateRoute,
		resolveCompanyBranch,
		showCallError,
		dataTable,
		linkGrid,
		portalCategoryGrid,
		loadRetailPosAssets,
		embedRetailPos,
		wrapLegacyDesk,
		defaultSidebar,
		switchLanguage,
		patientSearchBar,
		bindPatientSearch,
		alertList,
	});
})(window);
