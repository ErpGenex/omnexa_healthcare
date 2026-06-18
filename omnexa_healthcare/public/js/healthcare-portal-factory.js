/**
 * Native specialty portal factory — Journey shell + API data tables
 */
frappe.provide("omnexa_healthcare.portal");

omnexa_healthcare.portal.mount = function (wrapper, config) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare"));
		return;
	}
	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, config.deskTitle || config.titleEn || __("Portal"));

	async function render() {
		const args = Object.assign({ company, branch }, config.apiArgs || {});
		const data = config.api ? await OJ.call(config.api, args) : {};
		const kpis = (config.kpis || []).map((k) => ({
			value: data[k.field] ?? k.value ?? "—",
			label: OJ.t(k.labelAr, k.labelEn),
		}));
		if (data.count != null && !config.kpis?.length) {
			kpis.push({ value: data.count, label: OJ.t("السجلات", "Records") });
		}
		const $body = $("<div></div>");
		if (config.links) $body.append(OJ.linkGrid(config.links));
		if (config.columns && config.rowsField) {
			$body.append(`<h4>${OJ.t(config.tableTitleAr || "", config.tableTitleEn || "")}</h4>`);
			$body.append(
				OJ.dataTable(
					config.columns.map((c) => ({ field: c.field, label: OJ.t(c.ar, c.en) })),
					data[config.rowsField] || []
				)
			);
		}
		if (config.renderExtra) config.renderExtra($body, data);
		const $shell = OJ.shell({
			title: OJ.t(config.titleAr, config.titleEn),
			subtitle: OJ.t("Omnexa Healthcare", "Omnexa Healthcare"),
			role: OJ.t(config.roleAr || "", config.roleEn || ""),
			kpis,
			sidebar: OJ.defaultSidebar(config.sidebarRole || "nurse"),
			bodyEl: $body,
			homeRoute: config.homeRoute,
		});
		$mount.empty().append($shell);
	}

	render().catch((e) => OJ.showCallError(e));
};
