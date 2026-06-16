# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Blood bank operations — inventory, cross-match, issue."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def list_available_units(blood_group: str | None = None, branch: str | None = None, company: str | None = None) -> list[dict]:
	filters: dict = {"status": "Available", "expiry_date": [">=", today()]}
	if blood_group:
		filters["blood_group"] = blood_group
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Healthcare Blood Unit",
		filters=filters,
		fields=["name", "unit_number", "blood_group", "component", "expiry_date", "branch"],
		order_by="expiry_date asc",
		limit=100,
	)


@frappe.whitelist()
def approve_transfusion_order(order: str) -> dict:
	doc = frappe.get_doc("Healthcare Transfusion Order", order)
	if doc.status not in ("Draft", "Cross Match"):
		frappe.throw(_("Order cannot be approved from status {0}").format(doc.status))
	if doc.cross_match_result != "Compatible":
		frappe.throw(_("Cross match must be Compatible before approval."))
	doc.status = "Approved"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}
