frappe.pages["healthcare-patient-chart"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Patient Medical File"),
		single_column: true,
	});

	const $main = $(page.main);
	$main.html(`
		<div class="healthcare-patient-chart">
			<div class="row mb-3">
				<div class="col-md-8">
					<label class="text-muted small">${__("Patient")}</label>
					<div id="hpc-patient-picker"></div>
				</div>
				<div class="col-md-4 d-flex align-items-end">
					<button class="btn btn-primary" id="hpc-load">${__("Load file")}</button>
				</div>
			</div>
			<div id="hpc-summary" class="mb-3"></div>
			<div id="hpc-sections"></div>
		</div>
	`);

	const routeOpts = frappe.route_options || {};
	const $picker = $main.find("#hpc-patient-picker");
	const control = frappe.ui.form.make_control({
		df: { fieldtype: "Link", options: "Healthcare Patient", label: __("Patient") },
		parent: $picker.get(0),
		render_input: true,
	});
	control.set_value(routeOpts.patient || "");

	function section(title, rows, columns) {
		if (!rows || !rows.length) {
			return `<div class="card mb-3"><div class="card-header">${frappe.utils.escape_html(title)}</div><div class="card-body text-muted">${__(
				"No records"
			)}</div></div>`;
		}
		const head = columns.map((c) => `<th>${frappe.utils.escape_html(c.label)}</th>`).join("");
		const body = rows
			.map((row) => {
				const tds = columns
					.map((c) => `<td>${frappe.utils.escape_html(String(row[c.fieldname] ?? ""))}</td>`)
					.join("");
				return `<tr>${tds}</tr>`;
			})
			.join("");
		return `<div class="card mb-3"><div class="card-header">${frappe.utils.escape_html(title)} (${
			rows.length
		})</div><div class="card-body table-responsive"><table class="table table-sm table-bordered"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div></div>`;
	}

	async function load() {
		const patient = control.get_value();
		if (!patient) {
			frappe.msgprint(__("Select a patient"));
			return;
		}
		const r = await frappe.call({
			method: "omnexa_healthcare.api.patient_chart.get_patient_medical_file",
			args: { patient },
		});
		const data = r.message || {};
		const p = data.patient || {};
		$main.find("#hpc-summary").html(`
			<div class="alert alert-light border">
				<h5 class="mb-1">${frappe.utils.escape_html(p.full_name || patient)}</h5>
				<div class="small text-muted">
					${__("MRN")}: ${frappe.utils.escape_html(
						((p.identifiers || []).find((i) => i.identifier_type === "MRN") || {}).value || "—"
					)}
					· ${__("Gender")}: ${frappe.utils.escape_html(p.gender || "—")}
					· ${__("Birth date")}: ${frappe.utils.escape_html(p.birth_date || "—")}
				</div>
				<div class="small mt-2">${__("FHIR IPS document bundle loaded — international patient summary standard.")}</div>
			</div>
		`);

		$main.find("#hpc-sections").html(
			[
				section(__("Episodes of care"), data.episodes, [
					{ label: __("ID"), fieldname: "name" },
					{ label: __("Status"), fieldname: "status" },
					{ label: __("Start"), fieldname: "period_start" },
				]),
				section(__("Appointments"), data.appointments, [
					{ label: __("Date"), fieldname: "appointment_date" },
					{ label: __("Status"), fieldname: "status" },
					{ label: __("Channel"), fieldname: "booking_channel" },
					{ label: __("Practitioner"), fieldname: "practitioner" },
				]),
				section(__("Encounters"), data.encounters, [
					{ label: __("Start"), fieldname: "period_start" },
					{ label: __("Type"), fieldname: "encounter_type" },
					{ label: __("Status"), fieldname: "status" },
				]),
				section(__("Conditions (ICD-10)"), data.conditions, [
					{ label: __("Code"), fieldname: "icd10_code" },
					{ label: __("Description"), fieldname: "clinical_description" },
					{ label: __("Status"), fieldname: "clinical_status" },
				]),
				section(__("Allergies"), data.allergies, [
					{ label: __("Substance"), fieldname: "substance_text" },
					{ label: __("Criticality"), fieldname: "criticality" },
					{ label: __("Status"), fieldname: "clinical_status" },
				]),
				section(__("Medications"), data.medications, [
					{ label: __("Medication"), fieldname: "medication_text" },
					{ label: __("Dosage"), fieldname: "dosage_text" },
					{ label: __("Status"), fieldname: "status" },
				]),
				section(__("Vitals & observations"), data.observations, [
					{ label: __("Measure"), fieldname: "observation_profile" },
					{ label: __("Value"), fieldname: "value_primary" },
					{ label: __("When"), fieldname: "effective_datetime" },
				]),
				section(__("Lab & imaging reports"), data.diagnostic_reports, [
					{ label: __("Title"), fieldname: "report_title" },
					{ label: __("Category"), fieldname: "report_category" },
					{ label: __("Status"), fieldname: "status" },
					{ label: __("Date"), fieldname: "effective_datetime" },
				]),
				section(__("Admissions"), data.admissions, [
					{ label: __("Admitted"), fieldname: "admission_datetime" },
					{ label: __("Status"), fieldname: "status" },
					{ label: __("Bed"), fieldname: "bed" },
				]),
				section(__("ER visits"), data.er_visits, [
					{ label: __("Arrival"), fieldname: "arrival_datetime" },
					{ label: __("ESI"), fieldname: "esi_level" },
					{ label: __("Complaint"), fieldname: "chief_complaint" },
				]),
			].join("")
		);
	}

	$main.find("#hpc-load").on("click", () => load());
	if (routeOpts.patient) load();
};
