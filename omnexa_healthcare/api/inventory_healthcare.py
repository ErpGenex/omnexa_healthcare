# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare inventory — ward requisitions, OT consumables, par alerts."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


@frappe.whitelist()
def submit_ward_requisition(name: str) -> dict:
	doc = frappe.get_doc("Healthcare Ward Requisition", name)
	if doc.status != "Draft":
		frappe.throw(_("Only draft requisitions can be submitted"))
	doc.status = "Submitted"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def issue_ward_requisition(name: str, warehouse: str) -> dict:
	doc = frappe.get_doc("Healthcare Ward Requisition", name)
	if doc.status not in ("Submitted", "Draft"):
		frappe.throw(_("Requisition already processed"))
	se = frappe.new_doc("Stock Entry")
	se.company = doc.company
	se.branch = doc.branch
	se.purpose = "Material Transfer"
	se.posting_date = getdate(today())
	for row in doc.items:
		se.append("items", {"item": row.item, "qty": flt(row.qty), "s_warehouse": warehouse, "uom": row.uom})
	se.insert(ignore_permissions=True)
	se.submit()
	doc.db_set("status", "Issued")
	doc.db_set("stock_entry", se.name)
	return {"stock_entry": se.name, "requisition": doc.name}


@frappe.whitelist()
def issue_ot_consumable(name: str) -> dict:
	doc = frappe.get_doc("Healthcare Ot Consumable Issue", name)
	if doc.stock_entry:
		return {"stock_entry": doc.stock_entry, "created": False}
	se = frappe.new_doc("Stock Entry")
	se.company = doc.company
	se.branch = doc.branch
	se.purpose = "Material Issue"
	se.posting_date = getdate(doc.issue_date)
	se.append(
		"items",
		{"item": doc.item, "qty": flt(doc.qty), "s_warehouse": doc.warehouse, "uom": frappe.db.get_value("Item", doc.item, "stock_uom")},
	)
	se.insert(ignore_permissions=True)
	se.submit()
	doc.db_set("stock_entry", se.name)
	return {"stock_entry": se.name, "created": True}


@frappe.whitelist()
def get_par_level_alerts(company: str, branch: str | None = None) -> list[dict]:
	filters = {"company": company}
	if branch:
		filters["branch"] = branch
	rows = frappe.get_all("Healthcare Item Par Level", filters=filters, fields=["item", "warehouse", "par_level", "reorder_qty"])
	alerts = []
	for row in rows:
		on_hand = flt(frappe.db.get_value("Item", row.item, "current_stock_qty"))
		if on_hand < flt(row.par_level):
			alerts.append({**row, "on_hand": on_hand, "shortage": flt(row.par_level) - on_hand})
	return alerts
