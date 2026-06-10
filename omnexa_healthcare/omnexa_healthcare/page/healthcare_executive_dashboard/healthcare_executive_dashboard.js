frappe.pages["healthcare-executive-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Healthcare Executive Dashboard"),
		single_column: true,
	});

	const $body = $(page.body);
	$body.html(`<div class="text-muted">${__("Loading enterprise assessment…")}</div>`);

	frappe.call({
		method: "omnexa_healthcare.enterprise_assessment.get_enterprise_assessment",
		callback: (r) => {
			const a = r.message || {};
			const maturity = a.maturity || {};
			const gaps = a.gap_analysis || {};
			const ux = a.ux || {};
			const security = a.security || {};
			const functional = a.functional_audit || {};
			const counts = functional.counts || {};

			const domainRows = (maturity.domains || [])
				.map(
					(d) =>
						`<tr><td>${frappe.utils.escape_html(d.id)}</td><td>${d.score}%</td><td>${d.checks_passed}/${d.checks_total}</td></tr>`
				)
				.join("");

			$body.html(`
				<div class="row mb-3">
					<div class="col-md-3"><div class="card"><div class="card-body"><h6>${__("World-Class Score")}</h6><h3>${a.world_class_readiness_score || 0} / 5</h3><small>${__("Rank")} #${a.competitive_rank || "-"} / ${a.competitive_total || "-"}</small></div></div></div>
					<div class="col-md-3"><div class="card"><div class="card-body"><h6>${__("Maturity Index")}</h6><h3>${maturity.weighted_score || 0}%</h3><small>${__("Target")}: 95%</small></div></div></div>
					<div class="col-md-3"><div class="card"><div class="card-body"><h6>${__("Security Score")}</h6><h3>${security.score || 0}%</h3></div></div></div>
					<div class="col-md-3"><div class="card"><div class="card-body"><h6>${__("UX / UI / A11y")}</h6><h3>${ux.ux_score || 0} / ${ux.ui_score || 0} / ${ux.accessibility_score || 0}</h3></div></div></div>
				</div>
				<div class="row mb-3">
					<div class="col-md-12"><div class="card"><div class="card-header">${__("Platform Inventory")}</div><div class="card-body small">
						${__("DocTypes")}: ${counts.doctypes || 0} · ${__("Pages")}: ${counts.pages || 0} · ${__("Reports")}: ${counts.reports || 0} · ${__("Tests")}: ${counts.test_files || 0}
					</div></div></div>
				</div>
				<div class="row">
					<div class="col-md-7"><div class="card"><div class="card-header">${__("Maturity by Domain")}</div><div class="card-body p-0"><table class="table table-sm mb-0"><thead><tr><th>${__("Domain")}</th><th>${__("Score")}</th><th>${__("Checks")}</th></tr></thead><tbody>${domainRows}</tbody></table></div></div></div>
					<div class="col-md-5"><div class="card"><div class="card-header">${__("Open Gaps")}</div><div class="card-body small"><ul class="mb-0">${(gaps.strategic_gaps || []).map((g) => `<li><b>${frappe.utils.escape_html(g.feature)}</b> — ${frappe.utils.escape_html(g.priority)} (${frappe.utils.escape_html(g.status)})</li>`).join("")}</ul></div></div></div>
				</div>
			`);
		},
	});
};
