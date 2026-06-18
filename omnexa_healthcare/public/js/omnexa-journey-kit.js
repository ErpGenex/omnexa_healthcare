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
		const $root = $('<div class="oj-portal-catalog"></div>');
		(groups || []).forEach((g) => {
			const title = OJ.lang() === "ar" ? g.label_ar : g.label_en;
			const $sec = $(`<div class="oj-portal-section"><h4>${OJ.esc(title)}</h4><div class="oj-link-grid"></div></div>`);
			const $grid = $sec.find(".oj-link-grid");
			(g.portals || []).forEach((p) => {
				const label = OJ.lang() === "ar" ? p.label_ar : p.label_en;
				const $card = $(`<div class="oj-link-card ${p.exists === false ? "oj-muted-card" : ""}"><div class="oj-link-icon">${p.icon || "•"}</div><div class="oj-link-label">${OJ.esc(label)}</div><div class="oj-muted oj-link-sub">${OJ.esc((p.roles || []).join(", "))}</div></div>`);
				if (p.exists !== false) {
					$card.on("click", () => navigateRoute(p.route));
				}
				$grid.append($card);
			});
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
		const lang = currentLang();
		return `<div class="oj-user-menu">
			<button type="button" class="oj-user-btn" aria-haspopup="true" aria-expanded="false">
				<span class="oj-user-avatar">${OJ.esc((name || "U").charAt(0).toUpperCase())}</span>
				<span class="oj-user-name">${OJ.esc(name)}</span>
				<span class="oj-user-caret">▾</span>
			</button>
			<div class="oj-user-dropdown" role="menu">
				<div class="oj-user-dropdown-title">${OJ.t("الحساب", "Account")}</div>
				<a href="/app/user-profile" class="oj-user-dropdown-item" role="menuitem">⚙ ${OJ.t("الملف الشخصي", "Profile")}</a>
				<div class="oj-user-dropdown-divider"></div>
				<div class="oj-user-dropdown-title">${OJ.t("اللغة", "Language")}</div>
				<button type="button" class="oj-user-dropdown-item ${lang === "ar" ? "active" : ""}" data-oj-lang="ar" role="menuitem">🇸🇦 ${OJ.t("العربية", "Arabic")}</button>
				<button type="button" class="oj-user-dropdown-item ${lang === "en" ? "active" : ""}" data-oj-lang="en" role="menuitem">🇬🇧 English</button>
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
		$menu.find("[data-oj-lang]").on("click", function (e) {
			e.preventDefault();
			switchLanguage($(this).attr("data-oj-lang"));
		});
		$(document).on("click.ojUserMenu", () => $menu.removeClass("open"));
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
				{ id: "queue", label: OJ.t("الطابور", "Queue"), icon: "📋", route: "/app/healthcare-patient-queue" },
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
				{ id: "queue", label: OJ.t("الطابور", "Queue"), icon: "📋", route: "/app/healthcare-patient-queue" },
				{ id: "icu", label: OJ.t("ICU", "ICU"), icon: "🏥", route: "/app/healthcare-icu-board" },
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
	});
})(window);
