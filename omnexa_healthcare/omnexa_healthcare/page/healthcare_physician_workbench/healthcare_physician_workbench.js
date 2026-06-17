frappe.pages["healthcare-physician-workbench"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) return;
	const $mount = OJ.mountDeskPage(wrapper, __("Physician Workbench"));
	let patientCtrl;

	async function loadWorkbench(patient) {
		if (!patient) return;
		const data = await OJ.call("omnexa_healthcare.api.journey_desk.get_physician_workbench", { patient });
		const $emr = $(OJ.physicianModules(data));
		$emr.find(".oj-save-encounter").on("click", () => frappe.set_route("Form", "Healthcare Encounter", "new", { patient }));
		$mount.find(".oj-emr-mount").html($emr);
	}

	function render() {
		const $body = $(`
			<div class="oj-panel">
				<div class="oj-form-row"><div id="oj-physician-patient"></div></div>
			</div>
			<div class="oj-emr-mount"></div>
			<div class="oj-nav-actions">
				<a class="oj-btn oj-btn-outline" href="/app/healthcare-erx-writer">${OJ.t("روشتة إلكترونية", "ePrescription")}</a>
				<a class="oj-btn oj-btn-outline" href="/app/healthcare-patient-chart">${OJ.t("الملف الكامل", "Full Chart")}</a>
			</div>
		`);
		const $shell = OJ.shell({
			title: OJ.t("منصة الطبيب — EMR", "Physician Workbench — EMR"),
			subtitle: OJ.t("Clinical Excellence", "Clinical Excellence"),
			role: OJ.t("طبيب", "Physician"),
			sidebar: OJ.defaultSidebar("physician"),
			body: "",
		});
		$shell.find(".oj-body").append($body);
		$mount.empty().append($shell);
		patientCtrl = frappe.ui.form.make_control({
			parent: $body.find("#oj-physician-patient"),
			df: { fieldtype: "Link", options: "Healthcare Patient", label: OJ.t("المريض", "Patient"), reqd: 1 },
			render_input: true,
		});
		patientCtrl.$input.on("change", () => loadWorkbench(patientCtrl.get_value()));
	}

	render();
};
