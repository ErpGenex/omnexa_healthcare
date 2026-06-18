# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Blood bank operations — inventory, cross-match, issue."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import today


def _fields_for(doctype: str, candidates: list[str]) -> list[str]:
	return [f for f in candidates if frappe.db.has_column(doctype, f)]


def _blood_unit_list_fields() -> list[str]:
	return _fields_for(
		"Healthcare Blood Unit",
		["name", "unit_number", "blood_group", "component", "expiry_date", "branch", "status"],
	)


def _transfusion_order_list_fields() -> list[str]:
	return _fields_for(
		"Healthcare Transfusion Order",
		["name", "patient", "blood_unit", "cross_match_result", "status", "transfusion_datetime", "branch", "company"],
	)


def _enrich_transfusion_orders(orders: list[dict]) -> list[dict]:
	if not orders:
		return orders
	unit_ids = [o["blood_unit"] for o in orders if o.get("blood_unit")]
	unit_groups: dict[str, str] = {}
	if unit_ids and frappe.db.has_column("Healthcare Blood Unit", "blood_group"):
		for row in frappe.get_all(
			"Healthcare Blood Unit",
			filters={"name": ["in", unit_ids]},
			fields=["name", "blood_group"],
		):
			unit_groups[row.name] = row.blood_group or ""
	for row in orders:
		row["blood_group"] = unit_groups.get(row.get("blood_unit") or "", "")
		row["order_date"] = row.get("transfusion_datetime") or row.get("modified") or ""
		if row.get("patient") and not row.get("patient_name"):
			row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") or ""
	return orders


@frappe.whitelist()
def list_available_units(blood_group: str | None = None, branch: str | None = None, company: str | None = None) -> list[dict]:
	if not frappe.db.exists("DocType", "Healthcare Blood Unit"):
		return []
	filters: dict = {}
	if frappe.db.has_column("Healthcare Blood Unit", "status"):
		filters["status"] = "Available"
	if frappe.db.has_column("Healthcare Blood Unit", "expiry_date"):
		filters["expiry_date"] = [">=", today()]
	if blood_group and frappe.db.has_column("Healthcare Blood Unit", "blood_group"):
		filters["blood_group"] = blood_group
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Healthcare Blood Unit",
		filters=filters,
		fields=_blood_unit_list_fields() or ["name"],
		order_by="expiry_date asc" if frappe.db.has_column("Healthcare Blood Unit", "expiry_date") else "modified desc",
		limit=100,
	)


@frappe.whitelist()
def api_get_blood_bank_dashboard(branch: str | None = None, company: str | None = None) -> dict:
	units = list_available_units(branch=branch, company=company)
	orders = []
	if frappe.db.exists("DocType", "Healthcare Transfusion Order"):
		filters: dict = {}
		if branch:
			filters["branch"] = branch
		if company:
			filters["company"] = company
		orders = frappe.get_all(
			"Healthcare Transfusion Order",
			filters=filters,
			fields=_transfusion_order_list_fields() or ["name", "patient", "status"],
			order_by="modified desc",
			limit=30,
		)
		orders = _enrich_transfusion_orders(orders)
	return {"units": units, "orders": orders, "count": len(units)}


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
