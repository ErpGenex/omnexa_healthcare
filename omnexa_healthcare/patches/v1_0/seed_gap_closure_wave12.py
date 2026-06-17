# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def execute():
	try:
		from omnexa_healthcare.api.certification_export import export_certification_pack

		export_certification_pack()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave12 certification export")

	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "native_mobile_deferred"):
		settings.native_mobile_deferred = 1
	settings.save(ignore_permissions=True)
	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave12: certification pack (mobile deferred)")
