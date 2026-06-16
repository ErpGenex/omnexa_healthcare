# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave5_defs import DEFAULT_ICD11_CODES


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	for field in (
		"enable_blood_bank",
		"enable_cssd",
		"enable_physician_compensation",
		"enable_quality_capa",
		"enable_infection_surveillance",
	):
		if hasattr(settings, field):
			setattr(settings, field, 1)
	if hasattr(settings, "enable_icd11"):
		settings.enable_icd11 = 1
	settings.save(ignore_permissions=True)

	for code, desc, chapter, icd10_map in DEFAULT_ICD11_CODES:
		if frappe.db.exists("Healthcare Icd11 Code", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Healthcare Icd11 Code",
				"code": code,
				"description": desc,
				"chapter": chapter,
				"icd10_map": icd10_map,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	try:
		from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace

		sync_healthcare_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave5 workspace sync")

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave5: ICD-11 + wave4 settings + workspace")
