# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""DRG inpatient billing — assignment and package pricing."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def assign_drg_to_admission(admission: str, drg_code: str) -> dict:
	if not (admission and drg_code):
		frappe.throw(_("admission and drg_code are required"))
	if not frappe.db.exists("Healthcare Drg Code", drg_code):
		frappe.throw(_("DRG code {0} not found").format(drg_code))
	doc = frappe.get_doc("Healthcare Admission", admission)
	drg = frappe.get_doc("Healthcare Drg Code", drg_code)
	doc.db_set("drg_code", drg_code, update_modified=True)
	package_amount = flt(drg.base_rate) * flt(drg.weight or 1)
	return {
		"admission": admission,
		"drg_code": drg_code,
		"description": drg.description,
		"package_amount": package_amount,
	}


@frappe.whitelist()
def calculate_drg_revenue(admission: str) -> dict:
	doc = frappe.get_doc("Healthcare Admission", admission)
	drg_code = doc.get("drg_code")
	if not drg_code:
		return {"admission": admission, "drg_code": None, "package_amount": 0}
	drg = frappe.get_doc("Healthcare Drg Code", drg_code)
	package_amount = flt(drg.base_rate) * flt(drg.weight or 1)
	return {
		"admission": admission,
		"drg_code": drg_code,
		"weight": flt(drg.weight),
		"base_rate": flt(drg.base_rate),
		"package_amount": package_amount,
	}
