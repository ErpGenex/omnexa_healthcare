# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Family / dependents linked to guardian patient."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def list_dependents(guardian_patient: str) -> list[dict]:
	return frappe.get_all(
		"Healthcare Patient Dependent",
		filters={"guardian_patient": guardian_patient, "is_active": 1},
		fields=["name", "dependent_patient", "relationship", "is_active"],
		order_by="relationship asc",
	)


@frappe.whitelist()
def add_dependent(guardian_patient: str, dependent_patient: str, relationship: str, company: str) -> dict:
	if guardian_patient == dependent_patient:
		frappe.throw(_("Guardian and dependent must differ."), title=_("Dependents"))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Dependent",
			"guardian_patient": guardian_patient,
			"dependent_patient": dependent_patient,
			"relationship": relationship,
			"is_active": 1,
			"company": company,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "dependent": doc.name}
