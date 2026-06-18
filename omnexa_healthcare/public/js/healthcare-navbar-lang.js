/**
 * Desk navbar language switch — globe icon before Help dropdown.
 */
/* global frappe */
(function () {
	"use strict";

	const LANG_NAV_ID = "oj-navbar-lang-switch";

	function currentLang() {
		const bootLang = frappe.boot && frappe.boot.lang;
		if (bootLang === "ar" || bootLang === "en") return bootLang;
		return document.documentElement.lang === "ar" ? "ar" : "en";
	}

	function switchLanguage(langCode) {
		if (!langCode || langCode === currentLang()) return;
		const apply = () => {
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
		};
		if (window.OmnexaJourney && typeof OmnexaJourney.switchLanguage === "function") {
			OmnexaJourney.switchLanguage(langCode);
			return;
		}
		apply();
	}

	function langMenuHtml() {
		const lang = currentLang();
		return `<li class="nav-item dropdown dropdown-navbar-lang dropdown-mobile d-none d-lg-block" id="${LANG_NAV_ID}">
			<button
				type="button"
				class="btn-reset nav-link"
				data-toggle="dropdown"
				aria-controls="oj-toolbar-lang"
				aria-label="${frappe.utils.escape_html(__("Language"))}"
				title="${frappe.utils.escape_html(__("Language"))}"
			>
				<svg class="es-icon icon-sm" aria-hidden="true"><use href="#es-line-globe"></use></svg>
			</button>
			<div class="dropdown-menu dropdown-menu-right" id="oj-toolbar-lang" role="menu">
				<button type="button" class="btn-reset dropdown-item ${lang === "ar" ? "active" : ""}" data-oj-lang="ar" role="menuitem">
					<span class="oj-lang-flag" aria-hidden="true">🇸🇦</span> ${frappe.utils.escape_html(__("Arabic"))}
				</button>
				<button type="button" class="btn-reset dropdown-item ${lang === "en" ? "active" : ""}" data-oj-lang="en" role="menuitem">
					<span class="oj-lang-flag" aria-hidden="true">🇬🇧</span> English
				</button>
			</div>
		</li>`;
	}

	function bindLangMenu($li) {
		$li.find("[data-oj-lang]").on("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			switchLanguage($(this).attr("data-oj-lang"));
		});
	}

	function injectNavbarLang(tries) {
		if (document.getElementById(LANG_NAV_ID)) return;
		const helpLi = document.querySelector("li.dropdown-help");
		if (!helpLi || !helpLi.parentElement) {
			if ((tries || 0) > 40) return;
			setTimeout(() => injectNavbarLang((tries || 0) + 1), 250);
			return;
		}
		const $li = $(langMenuHtml());
		bindLangMenu($li);
		helpLi.parentElement.insertBefore($li.get(0), helpLi);
	}

	frappe.ready(() => {
		if (!frappe.session || frappe.session.user === "Guest") return;
		injectNavbarLang(0);
	});
})();
