# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Bridge Healthcare Practitioner to HR / shifts when omnexa_hr is installed."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_practitioner_shift_context(practitioner: str) -> dict:
	if not practitioner:
		frappe.throw(_("practitioner is required"))
	pr = frappe.get_doc("Healthcare Practitioner", practitioner)
	out = {"practitioner": practitioner, "user": pr.user, "license_number": pr.license_number, "shifts": []}
	if not frappe.db.exists("DocType", "Shift Assignment"):
		out["hr_app"] = None
		return out
	out["hr_app"] = "omnexa_hr"
	if pr.user:
		out["shifts"] = frappe.get_all(
			"Shift Assignment",
			filters={"employee": frappe.db.get_value("Employee", {"user_id": pr.user}, "name")},
			fields=["shift_type", "start_date", "end_date"],
			limit=10,
		)
	return out
