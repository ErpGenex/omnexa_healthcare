# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_fhir_bulk_export"):
		settings.enable_fhir_bulk_export = 1
	if hasattr(settings, "enable_hl7_mllp"):
		settings.enable_hl7_mllp = 1
	settings.save(ignore_permissions=True)
	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave10: FHIR bulk + HL7 MLLP flags")
