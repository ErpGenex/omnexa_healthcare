# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave7_defs import GAP_CLOSURE_WAVE7_DOCTYPES, RXNORM_BASE_DRUGS, RXNORM_FORMS, RXNORM_STRENGTHS


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_erx"):
		settings.enable_erx = 1
	settings.save(ignore_permissions=True)

	count = 0
	for cui, drug, generic in RXNORM_BASE_DRUGS:
		for strength in RXNORM_STRENGTHS:
			for form in RXNORM_FORMS:
				code = f"{cui}-{frappe.scrub(strength)}-{frappe.scrub(form)}"
				if frappe.db.exists("Healthcare Rxnorm Code", code):
					continue
				frappe.get_doc(
					{
						"doctype": "Healthcare Rxnorm Code",
						"rxnorm_cui": code,
						"drug_name": f"{drug} {strength} {form}",
						"generic_name": generic,
						"strength": strength,
						"dosage_form": form,
						"is_active": 1,
					}
				).insert(ignore_permissions=True)
				count += 1
				if count >= 1200:
					break
			if count >= 1200:
				break
		if count >= 1200:
			break

	for cui, drug, generic in RXNORM_BASE_DRUGS[:20]:
		code = f"FORM-{cui}"
		if frappe.db.exists("Healthcare Drug Formulary", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Healthcare Drug Formulary",
				"formulary_code": code,
				"drug_name": drug,
				"generic_name": generic,
				"rxnorm_code": frappe.db.get_value("Healthcare Rxnorm Code", {"drug_name": ["like", f"{drug}%"]}, "name"),
				"is_active": 1,
				"max_daily_dose": 1000,
				"pregnancy_category": "C" if "warfarin" in generic.lower() else "B",
			}
		).insert(ignore_permissions=True)

	try:
		from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace

		sync_healthcare_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave7 workspace sync")

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave7: RxNorm %s codes + eRx settings", count)
