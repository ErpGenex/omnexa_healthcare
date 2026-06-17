# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave8_defs import DEFAULT_CDS_RULES, SNOMED_WAVE8_SUBSET


def execute():
	for name, trigger, match, severity in DEFAULT_CDS_RULES:
		if frappe.db.exists("Healthcare Clinical Cds Rule", {"rule_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Healthcare Clinical Cds Rule",
				"rule_name": name,
				"trigger_event": trigger,
				"match_field": match,
				"severity": severity,
				"message": name,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	for cid, term in SNOMED_WAVE8_SUBSET:
		if frappe.db.exists("Healthcare Snomed Code", {"concept_id": cid}):
			continue
		frappe.get_doc({"doctype": "Healthcare Snomed Code", "concept_id": cid, "term": term, "is_active": 1}).insert(
			ignore_permissions=True
		)

	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_advanced_cds"):
		settings.enable_advanced_cds = 1
	settings.save(ignore_permissions=True)
	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave8: CDS rules + SNOMED subset")
