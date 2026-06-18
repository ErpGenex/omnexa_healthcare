# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared ERP helpers for clinical department desks (lab, radiology, dental)."""

from __future__ import annotations

import frappe
from frappe.utils import flt, today


def resolve_company_branch(company: str | None, branch: str | None) -> tuple[str, str]:
	company = (company or "").strip() or frappe.defaults.get_user_default("Company") or ""
	branch = (branch or "").strip() or frappe.defaults.get_user_default("Branch") or ""
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or ""
	return company, branch


def safe_doctype_fields(doctype: str, fields: list[str]) -> list[str]:
	"""Return only fields that exist on the DocType table (avoids migrate drift errors)."""
	out: list[str] = []
	for field in fields:
		if field == "name" or frappe.db.has_column(doctype, field):
			out.append(field)
	return out or ["name"]


def item_code(item: str) -> str:
	return frappe.db.get_value("Item", item, "item_code") or item


def warehouse_qty(item: str, warehouse: str) -> float:
	code = item_code(item)
	if not code or not warehouse:
		return 0.0
	if frappe.db.exists("DocType", "Stock Ledger Entry"):
		return flt(
			frappe.db.sql(
				"""
				SELECT IFNULL(SUM(actual_qty), 0)
				FROM `tabStock Ledger Entry`
				WHERE item_code = %s AND warehouse = %s
				""",
				(code, warehouse),
			)[0][0]
		)
	return flt(frappe.db.get_value("Item", item, "current_stock_qty"))


def default_department_warehouse(company: str, patterns: list[str]) -> str | None:
	for pattern in patterns:
		wh = frappe.db.get_value(
			"Warehouse",
			{"company": company, "warehouse_name": ["like", pattern]},
			"name",
			order_by="creation desc",
		)
		if wh:
			return wh
	return frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")


def get_accounts_summary(company: str, branch: str | None = None, limit: int = 15) -> dict:
	limit = min(int(limit or 15), 50)
	out: dict = {"sales_invoices": [], "payment_entries": [], "revenue_today": 0.0, "collections_today": 0.0}
	if frappe.db.exists("DocType", "Sales Invoice"):
		filters = {"company": company, "docstatus": 1}
		si_fields = ["name", "customer", "posting_date", "grand_total", "docstatus"]
		if frappe.db.has_column("Sales Invoice", "status"):
			si_fields.append("status")
		out["sales_invoices"] = frappe.get_all(
			"Sales Invoice",
			filters=filters,
			fields=si_fields,
			order_by="posting_date desc",
			limit=limit,
		)
		for row in out["sales_invoices"]:
			if "status" not in row:
				row["status"] = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(row.get("docstatus"), "")
		out["revenue_today"] = flt(
			frappe.db.sql(
				"""
				SELECT IFNULL(SUM(grand_total), 0) FROM `tabSales Invoice`
				WHERE company = %s AND docstatus = 1 AND posting_date = %s
				""",
				(company, today()),
			)[0][0]
		)
	if frappe.db.exists("DocType", "Payment Entry"):
		pe_filters = {"company": company, "docstatus": 1}
		if frappe.db.has_column("Payment Entry", "payment_type"):
			pe_filters["payment_type"] = "Receive"
		pe_fields = ["name", "posting_date", "paid_amount"]
		if frappe.db.has_column("Payment Entry", "party"):
			pe_fields.append("party")
		if frappe.db.has_column("Payment Entry", "mode_of_payment"):
			pe_fields.append("mode_of_payment")
		out["payment_entries"] = frappe.get_all(
			"Payment Entry",
			filters=pe_filters,
			fields=pe_fields,
			order_by="posting_date desc",
			limit=limit,
		)
	return out


def get_purchases_summary(company: str, limit: int = 15) -> dict:
	limit = min(int(limit or 15), 50)
	out: dict = {"purchase_orders": [], "stock_entries": []}
	if frappe.db.exists("DocType", "Purchase Order"):
		po_fields = ["name", "supplier", "grand_total", "docstatus"]
		date_field = "transaction_date" if frappe.db.has_column("Purchase Order", "transaction_date") else "posting_date"
		if frappe.db.has_column("Purchase Order", date_field):
			po_fields.append(date_field)
		if frappe.db.has_column("Purchase Order", "status"):
			po_fields.append("status")
		out["purchase_orders"] = frappe.get_all(
			"Purchase Order",
			filters={"company": company},
			fields=po_fields,
			order_by="modified desc",
			limit=limit,
		)
		for row in out["purchase_orders"]:
			if date_field in row and "transaction_date" not in row:
				row["transaction_date"] = row.get(date_field)
			if "status" not in row:
				row["status"] = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(row.get("docstatus"), "")
	if frappe.db.exists("DocType", "Stock Entry"):
		se_fields = ["name", "posting_date", "purpose"]
		if frappe.db.has_column("Stock Entry", "total_amount"):
			se_fields.append("total_amount")
		out["stock_entries"] = frappe.get_all(
			"Stock Entry",
			filters={"company": company, "docstatus": 1},
			fields=se_fields,
			order_by="posting_date desc",
			limit=limit,
		)
	return out


def get_stock_rows(company: str, warehouse: str | None, item_prefix: str | None = None, limit: int = 30) -> list[dict]:
	filters: dict = {"company": company, "is_stock_item": 1}
	if item_prefix:
		filters["item_code"] = ["like", f"{item_prefix}%"]
	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=["name", "item_code", "item_name"],
		order_by="item_name asc",
		limit=limit,
	)
	for row in rows:
		row["on_hand"] = warehouse_qty(row.name, warehouse) if warehouse else 0
	return rows
