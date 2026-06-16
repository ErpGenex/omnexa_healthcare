frappe.pages["healthcare-family-medicine-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Family Medicine Dashboard"),
		single_column: true,
	});
	const $root = $(`<div class="hc-fm-dashboard"></div>`).appendTo(page.body);
	const $filters = $(`<div class="row mb-3"></div>`).appendTo($root);
	const familyUnit = frappe.ui.form.make_control({
		parent: $filters,
		df: { fieldtype: "Link", options: "Healthcare Family Unit", label: __("Family unit"), reqd: 1 },
		render_input: true,
	});
	const $grid = $(`<div class="row" id="hc-fm-widgets"></div>`).appendTo($root);

	function widget(title, id) {
		return $(`<div class="col-md-6 mb-3"><div class="card h-100"><div class="card-header"><strong>${title}</strong></div><div class="card-body" id="${id}"></div></div></div>`);
	}

	const $members = widget(__("Household members"), "hc-fm-members");
	const $alerts = widget(__("Risk & preventive alerts"), "hc-fm-alerts");
	const $chronic = widget(__("Chronic conditions"), "hc-fm-chronic");
	const $encounters = widget(__("Open encounters"), "hc-fm-encounters");
	const $preventive = widget(__("Preventive care"), "hc-fm-preventive");
	const $risk = widget(__("Risk scores"), "hc-fm-risk");
	$grid.append($members, $alerts, $chronic, $encounters, $preventive, $risk);

	function table(rows, cols) {
		if (!rows.length) return `<p class="text-muted">${__("None")}</p>`;
		let html = `<table class="table table-sm table-bordered"><thead><tr>`;
		cols.forEach((c) => { html += `<th>${c.label}</th>`; });
		html += `</tr></thead><tbody>`;
		rows.forEach((r) => {
			html += `<tr>`;
			cols.forEach((c) => {
				const val = c.format ? c.format(r) : frappe.utils.escape_html(String(r[c.field] ?? ""));
				html += `<td>${val}</td>`;
			});
			html += `</tr>`;
		});
		html += `</tbody></table>`;
		return html;
	}

	function render(data) {
		$("#hc-fm-members").html(
			table(data.members || [], [
				{ field: "patient_name", label: __("Name") },
				{ field: "relationship", label: __("Relationship") },
				{ field: "gender", label: __("Gender") },
			])
		);
		$("#hc-fm-alerts").html(
			table(data.alerts || [], [
				{ field: "level", label: __("Level") },
				{ field: "message", label: __("Alert") },
			])
		);
		$("#hc-fm-chronic").html(
			table(data.chronic_conditions || [], [
				{ field: "patient", label: __("Patient") },
				{ field: "description", label: __("Condition") },
				{ field: "clinical_status", label: __("Status") },
			])
		);
		$("#hc-fm-encounters").html(
			table(data.open_encounters || [], [
				{ field: "patient", label: __("Patient") },
				{ field: "encounter_date", label: __("Date") },
				{ field: "status", label: __("Status") },
			])
		);
		$("#hc-fm-preventive").html(
			table(data.preventive_plans || [], [
				{ field: "plan_title", label: __("Plan") },
				{ field: "patient", label: __("Patient") },
				{ field: "status", label: __("Status") },
			])
		);
		$("#hc-fm-risk").html(
			table(data.risk_scores || [], [
				{ field: "assessment_date", label: __("Date") },
				{ field: "cardiovascular_risk_score", label: __("CV %") },
				{ field: "diabetes_risk_score", label: __("DM %") },
				{ field: "overall_risk_level", label: __("Level") },
			])
		);
	}

	function load() {
		const fu = familyUnit.get_value();
		if (!fu) return frappe.msgprint(__("Select a family unit"));
		frappe.call({
			method: "omnexa_healthcare.api.family_unit.get_family_dashboard",
			args: { family_unit: fu },
			callback(r) { render(r.message || {}); },
		});
	}

	page.set_primary_action(__("Load dashboard"), load);
	page.add_menu_item(__("Compute risk score"), () => {
		const fu = familyUnit.get_value();
		if (!fu) return frappe.msgprint(__("Select a family unit"));
		frappe.call({
			method: "omnexa_healthcare.api.family_risk_engine.compute_family_risk",
			args: { family_unit: fu },
			callback() {
				frappe.show_alert({ message: __("Risk score computed"), indicator: "green" });
				load();
			},
		});
	});
	page.add_menu_item(__("Open family tree"), () => {
		const fu = familyUnit.get_value();
		if (fu) frappe.set_route("healthcare-family-tree", { family_unit: fu });
	});
	page.add_menu_item(__("New family unit"), () => frappe.new_doc("Healthcare Family Unit"));
};
