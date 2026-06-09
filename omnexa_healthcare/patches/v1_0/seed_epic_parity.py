# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Seed CDS rules, SNOMED samples, and default ER/AI configuration."""

import frappe


CDS = [
	("Penicillin allergy check", "Medication Order", "penicillin", "Critical", "Patient may have penicillin allergy — verify."),
	("Contrast allergy", "Lab Order", "contrast", "Warning", "Check contrast allergy before imaging."),
]

SNOMED = [
	("38341003", "Hypertensive disorder"),
	("73211009", "Diabetes mellitus"),
	("195967001", "Asthma"),
]


def execute():
	for name, trigger, match, severity, message in CDS:
		if frappe.db.exists("Healthcare Clinical Cds Rule", {"rule_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Healthcare Clinical Cds Rule",
				"rule_name": name,
				"trigger_event": trigger,
				"match_field": match,
				"severity": severity,
				"message": message,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
	for cid, term in SNOMED:
		if frappe.db.exists("Healthcare Snomed Code", {"concept_id": cid}):
			continue
		frappe.get_doc({"doctype": "Healthcare Snomed Code", "concept_id": cid, "term": term, "is_active": 1}).insert(
			ignore_permissions=True
		)
