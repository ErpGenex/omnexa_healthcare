# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_predictive_analytics_v2"):
		settings.enable_predictive_analytics_v2 = 1
	if hasattr(settings, "enable_care_gap_automation"):
		settings.enable_care_gap_automation = 1
	settings.save(ignore_permissions=True)

	try:
		from omnexa_healthcare.api.care_gap_automation import detect_care_gaps

		detect_care_gaps(limit=10)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave11 care gap dry run")

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave11: BI + AI automation")
