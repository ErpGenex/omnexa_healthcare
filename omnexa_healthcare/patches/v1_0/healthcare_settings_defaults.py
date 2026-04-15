# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe


def execute():
	"""One-time: Checkbox Singles can be stored as 0 on first sync; default is allow meds without encounter."""
	if not frappe.db.exists("DocType", "Healthcare Settings"):
		return
	frappe.db.set_single_value(
		"Healthcare Settings", "allow_medication_statement_without_encounter", 1, update_modified=False
	)
