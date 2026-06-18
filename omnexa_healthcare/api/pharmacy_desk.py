# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Pharmacy desk — POS, inventory, purchases, stock transfers."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, today

from omnexa_healthcare.api.inventory_healthcare import get_par_level_alerts
from omnexa_healthcare.api.pharmacy import api_check_drug_interactions, api_pharmacy_pos_dispense, api_select_fefo_batch


def _resolve_company_branch(company: str | None, branch: str | None) -> tuple[str, str]:
	company = (company or "").strip() or frappe.defaults.get_user_default("Company") or ""
	branch = (branch or "").strip() or frappe.defaults.get_user_default("Branch") or ""
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or ""
	return company, branch


def _item_code(item: str) -> str:
	return frappe.db.get_value("Item", item, "item_code") or item


def _warehouse_qty(item: str, warehouse: str) -> float:
	item_code = _item_code(item)
	if not item_code or not warehouse:
		return 0.0
	if frappe.db.exists("DocType", "Stock Ledger Entry"):
		return flt(
			frappe.db.sql(
				"""
				SELECT IFNULL(SUM(actual_qty), 0)
				FROM `tabStock Ledger Entry`
				WHERE item_code = %s AND warehouse = %s
				""",
				(item_code, warehouse),
			)[0][0]
		)
	return flt(frappe.db.get_value("Item", item, "current_stock_qty"))


def _default_pharmacy_warehouse(company: str, branch: str | None = None) -> str | None:
	for pattern in ("%Pharmacy WH%", "%PHARMACY%", "DEMO-HC%"):
		wh = frappe.db.get_value(
			"Warehouse",
			{"company": company, "warehouse_name": ["like", pattern]},
			"name",
			order_by="creation desc",
		)
		if wh:
			return wh
	return frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")


def _resolve_item_for_medication(medication_text: str, company: str) -> dict | None:
	text = (medication_text or "").strip().lower()
	if not text:
		return None

	if frappe.db.has_column("Healthcare Drug Formulary", "default_item"):
		for row in frappe.get_all(
			"Healthcare Drug Formulary",
			filters={"is_active": 1},
			fields=["drug_name", "generic_name", "default_item", "formulary_code"],
			limit=200,
		):
			for token in (row.drug_name, row.generic_name):
				if token and token.lower() in text and row.default_item:
					return {
						"item": row.default_item,
						"item_code": _item_code(row.default_item),
						"label": row.drug_name,
						"source": "formulary",
					}

	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER, PHARMACY_ITEMS

	for code, label, rate in PHARMACY_ITEMS:
		if label.lower() in text or code.lower() in text:
			item_code = f"{DEMO_MARKER}{code}"
			item_name = frappe.db.get_value("Item", {"item_code": item_code, "company": company}, "name")
			if item_name:
				return {
					"item": item_name,
					"item_code": item_code,
					"label": label,
					"rate": rate,
					"source": "demo_item",
				}
	return None


@frappe.whitelist()
def get_pharmacy_full_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	warehouse = _default_pharmacy_warehouse(company, branch)
	patient_filter = {"branch": branch} if branch else {}
	rx_pending = frappe.db.count(
		"Healthcare Medication Statement",
		{**patient_filter, "status": ["in", ["active", "Active", "draft", "Draft"]]},
	)
	dispense_filters = {"creation": [">=", f"{today()} 00:00:00"]}
	if branch and frappe.db.has_column("Healthcare Medication Dispense", "branch"):
		dispense_filters["branch"] = branch
	dispensed_today = frappe.db.count("Healthcare Medication Dispense", dispense_filters)
	alerts = get_par_level_alerts(company, branch) if company else []
	orders = frappe.get_all(
		"Healthcare Medication Statement",
		filters={**patient_filter, "status": ["in", ["active", "Active", "draft", "Draft"]]},
		fields=["name", "patient", "medication_text", "dosage_text", "status"],
		order_by="modified desc",
		limit=12,
	)
	for row in orders:
		row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") or row.patient
		resolved = _resolve_item_for_medication(row.medication_text, company)
		row["resolved_item"] = resolved.get("item") if resolved else None
		row["item_label"] = resolved.get("label") if resolved else ""
		if warehouse and row.get("resolved_item"):
			row["on_hand"] = _warehouse_qty(row["resolved_item"], warehouse)
			row["can_dispense"] = row["on_hand"] > 0
		else:
			row["on_hand"] = 0
			row["can_dispense"] = False

	stock_rows = []
	if warehouse:
		for par in frappe.get_all(
			"Healthcare Item Par Level",
			filters={"company": company, **({"branch": branch} if branch else {})},
			fields=["item", "par_level", "reorder_qty"],
			limit=30,
		):
			on_hand = _warehouse_qty(par.item, warehouse)
			stock_rows.append(
				{
					"item": par.item,
					"item_code": _item_code(par.item),
					"item_name": frappe.db.get_value("Item", par.item, "item_name") or par.item,
					"on_hand": on_hand,
					"par_level": flt(par.par_level),
					"reorder_qty": flt(par.reorder_qty),
					"below_par": on_hand < flt(par.par_level),
				}
			)

	return {
		"company": company,
		"branch": branch,
		"warehouse": warehouse,
		"orders_pending": rx_pending,
		"dispensed_today": dispensed_today,
		"low_stock_items": len(alerts),
		"par_alerts": alerts[:20],
		"orders": orders,
		"stock_rows": stock_rows,
		"warehouses": frappe.get_all(
			"Warehouse",
			filters={"company": company, "is_group": 0},
			fields=["name", "warehouse_name"],
			limit=20,
		),
	}


@frappe.whitelist()
def search_pharmacy_pos_items(query: str = "", company: str | None = None, warehouse: str | None = None, limit: int = 20) -> list[dict]:
	company, _branch = _resolve_company_branch(company, None)
	warehouse = warehouse or _default_pharmacy_warehouse(company)
	limit = min(cint(limit) or 20, 50)
	q = (query or "").strip()
	filters: dict = {"company": company, "is_stock_item": 1}
	if q:
		filters["item_name"] = ["like", f"%{q}%"]
	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=["name", "item_code", "item_name", "standard_rate"],
		order_by="item_name asc",
		limit=limit,
	)
	for row in rows:
		row["on_hand"] = _warehouse_qty(row.name, warehouse) if warehouse else flt(
			frappe.db.get_value("Item", row.name, "current_stock_qty")
		)
		row["rate"] = flt(row.standard_rate)
	return rows


@frappe.whitelist()
def get_patient_prescriptions_enriched(patient: str, company: str | None = None, warehouse: str | None = None) -> list[dict]:
	company, branch = _resolve_company_branch(company, None)
	warehouse = warehouse or _default_pharmacy_warehouse(company, branch)
	rows = frappe.get_all(
		"Healthcare Medication Statement",
		filters={"patient": patient, "status": ["in", ["active", "Active", "draft", "Draft"]]},
		fields=["name", "medication_text", "dosage_text", "status", "encounter", "modified"],
		order_by="modified desc",
		limit=20,
	)
	for row in rows:
		resolved = _resolve_item_for_medication(row.medication_text, company)
		row["resolved_item"] = resolved.get("item") if resolved else None
		row["item_label"] = resolved.get("label") if resolved else ""
		row["rate"] = flt(resolved.get("rate")) if resolved else 0
		if row.get("resolved_item") and warehouse:
			row["on_hand"] = _warehouse_qty(row["resolved_item"], warehouse)
			batch = api_select_fefo_batch(row["resolved_item"], warehouse, 1)
			row["batch_no"] = batch.get("batch_no")
			row["expiry_date"] = batch.get("expiry_date")
			row["can_dispense"] = row["on_hand"] > 0
		else:
			row["on_hand"] = 0
			row["can_dispense"] = False
	return rows


@frappe.whitelist()
def defer_prescription(medication_statement: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Medication Statement", medication_statement)
	doc.status = "on-hold"
	if reason and frappe.db.has_column("Healthcare Medication Statement", "note"):
		doc.note = reason
	doc.save(ignore_permissions=True)
	return {"ok": True, "name": doc.name, "status": doc.status}


@frappe.whitelist()
def pharmacy_pos_checkout(
	patient: str,
	lines: str | list,
	warehouse: str | None = None,
	company: str | None = None,
	branch: str | None = None,
	payment_method: str = "Cash",
) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	warehouse = warehouse or _default_pharmacy_warehouse(company, branch)
	if not warehouse:
		frappe.throw(_("Pharmacy warehouse not configured."), title=_("Warehouse"))
	if isinstance(lines, str):
		lines = json.loads(lines)
	if not lines:
		frappe.throw(_("Cart is empty."))

	results = []
	total = 0.0
	for line in lines:
		item = line.get("item")
		qty = flt(line.get("qty") or 1)
		if not item or qty <= 0:
			continue
		on_hand = _warehouse_qty(item, warehouse)
		if on_hand < qty:
			frappe.throw(
				_("Insufficient stock for {0} (available: {1}).").format(_item_code(item), on_hand),
				title=_("Stock"),
			)
		out = api_pharmacy_pos_dispense(patient, item, qty, warehouse, branch, company)
		rate = flt(line.get("rate") or frappe.db.get_value("Item", item, "standard_rate"))
		total += rate * qty
		results.append({**out, "item": item, "qty": qty, "rate": rate})

	return {
		"ok": True,
		"patient": patient,
		"warehouse": warehouse,
		"payment_method": payment_method,
		"total_amount": total,
		"lines": results,
	}


@frappe.whitelist()
def create_pharmacy_purchase_receipt(
	warehouse: str,
	items: str | list,
	company: str | None = None,
	branch: str | None = None,
	supplier: str | None = None,
	remarks: str | None = None,
) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	if isinstance(items, str):
		items = json.loads(items)
	if not warehouse or not items:
		frappe.throw(_("Warehouse and items are required."))

	se = frappe.new_doc("Stock Entry")
	se.company = company
	if frappe.get_meta("Stock Entry").has_field("branch"):
		se.branch = branch
	se.posting_date = getdate(today())
	se.purpose = "Material Receipt"
	if frappe.get_meta("Stock Entry").has_field("to_warehouse"):
		se.to_warehouse = warehouse
	se.remarks = remarks or _("Pharmacy purchase receipt")

	for line in items:
		item = line.get("item")
		qty = flt(line.get("qty"))
		rate = flt(line.get("rate"))
		if not item or qty <= 0:
			continue
		item_doc = frappe.get_doc("Item", item)
		row = {
			"item": item,
			"item_code": item_doc.item_code,
			"qty": qty,
			"t_warehouse": warehouse,
			"uom": item_doc.stock_uom,
		}
		if frappe.get_meta("Stock Entry Item").has_field("rate"):
			row["rate"] = rate
		elif frappe.get_meta("Stock Entry Item").has_field("basic_rate"):
			row["basic_rate"] = rate
		se.append("items", row)

	if not se.items:
		frappe.throw(_("No valid purchase lines."))
	se.insert(ignore_permissions=True)
	se.submit()

	po_name = None
	if supplier and frappe.db.exists("DocType", "Purchase Order"):
		try:
			po = frappe.get_doc(
				{
					"doctype": "Purchase Order",
					"company": company,
					"supplier": supplier,
					"transaction_date": today(),
					"items": [
						{
							"item": line.item,
							"qty": line.qty,
							"rate": flt(line.rate),
							"warehouse": warehouse,
						}
						for line in se.items
					],
				}
			)
			po.insert(ignore_permissions=True)
			po_name = po.name
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Pharmacy PO create skipped")

	return {"stock_entry": se.name, "purchase_order": po_name, "warehouse": warehouse}


@frappe.whitelist()
def create_pharmacy_stock_transfer(
	source_warehouse: str,
	target_warehouse: str,
	items: str | list,
	company: str | None = None,
	branch: str | None = None,
	remarks: str | None = None,
) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	if isinstance(items, str):
		items = json.loads(items)
	if not source_warehouse or not target_warehouse or source_warehouse == target_warehouse:
		frappe.throw(_("Source and target warehouses must differ."))
	if not items:
		frappe.throw(_("Transfer lines are required."))

	se = frappe.new_doc("Stock Entry")
	se.company = company
	if frappe.get_meta("Stock Entry").has_field("branch"):
		se.branch = branch
	se.posting_date = getdate(today())
	se.purpose = "Material Transfer"
	se.remarks = remarks or _("Pharmacy stock transfer")

	for line in items:
		item = line.get("item")
		qty = flt(line.get("qty"))
		if not item or qty <= 0:
			continue
		on_hand = _warehouse_qty(item, source_warehouse)
		if on_hand < qty:
			frappe.throw(
				_("Insufficient stock in {0} for {1} (available: {2}).").format(
					source_warehouse, _item_code(item), on_hand
				),
				title=_("Stock"),
			)
		item_doc = frappe.get_doc("Item", item)
		se.append(
			"items",
			{
				"item": item,
				"item_code": item_doc.item_code,
				"qty": qty,
				"s_warehouse": source_warehouse,
				"t_warehouse": target_warehouse,
				"uom": item_doc.stock_uom,
			},
		)

	if not se.items:
		frappe.throw(_("No valid transfer lines."))
	se.insert(ignore_permissions=True)
	se.submit()
	return {"stock_entry": se.name, "source_warehouse": source_warehouse, "target_warehouse": target_warehouse}


@frappe.whitelist()
def link_formulary_to_demo_items(company: str | None = None) -> dict:
	"""Map formulary drugs to demo Item codes for dispensing."""
	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER, PHARMACY_ITEMS

	company, _ = _resolve_company_branch(company, None)
	if not frappe.db.has_column("Healthcare Drug Formulary", "default_item"):
		return {"ok": False, "error": "default_item field missing — run migrate"}

	linked = 0
	for code, label, _rate in PHARMACY_ITEMS[:5]:
		item_name = frappe.db.get_value("Item", {"item_code": f"{DEMO_MARKER}{code}", "company": company}, "name")
		if not item_name:
			continue
		for formulary in frappe.get_all(
			"Healthcare Drug Formulary",
			filters={"is_active": 1, "drug_name": ["like", f"%{label.split()[0]}%"]},
			pluck="name",
			limit=3,
		):
			frappe.db.set_value("Healthcare Drug Formulary", formulary, "default_item", item_name, update_modified=False)
			linked += 1
	return {"ok": True, "linked": linked}


@frappe.whitelist()
def get_pharmacy_accounts_summary(company: str | None = None, branch: str | None = None, limit: int = 15) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	limit = min(int(limit or 15), 50)
	out: dict = {"sales_invoices": [], "payment_entries": [], "revenue_today": 0.0, "collections_today": 0.0}
	if frappe.db.exists("DocType", "Sales Invoice"):
		filters = {"company": company, "docstatus": 1}
		out["sales_invoices"] = frappe.get_all(
			"Sales Invoice", filters=filters,
			fields=["name", "customer", "posting_date", "grand_total", "status"],
			order_by="posting_date desc", limit=limit,
		)
	if frappe.db.exists("DocType", "Payment Entry"):
		out["payment_entries"] = frappe.get_all(
			"Payment Entry",
			filters={"company": company, "docstatus": 1, "payment_type": "Receive"},
			fields=["name", "party", "posting_date", "paid_amount", "mode_of_payment"],
			order_by="posting_date desc", limit=limit,
		)
	return out


@frappe.whitelist()
def get_pharmacy_purchases_summary(company: str | None = None, branch: str | None = None, limit: int = 15) -> dict:
	company, _branch = _resolve_company_branch(company, branch)
	limit = min(int(limit or 15), 50)
	out: dict = {"purchase_orders": [], "material_receipts": []}
	if frappe.db.exists("DocType", "Purchase Order"):
		out["purchase_orders"] = frappe.get_all(
			"Purchase Order", filters={"company": company},
			fields=["name", "supplier", "transaction_date", "grand_total", "status"],
			order_by="transaction_date desc", limit=limit,
		)
	if frappe.db.exists("DocType", "Stock Entry"):
		out["material_receipts"] = frappe.get_all(
			"Stock Entry",
			filters={"company": company, "purpose": "Material Receipt", "docstatus": 1},
			fields=["name", "posting_date", "total_amount", "remarks"],
			order_by="posting_date desc", limit=limit,
		)
	return out


@frappe.whitelist()
def link_retail_pos_patient_sale(patient: str, sales_invoice: str, warehouse: str | None = None, company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	warehouse = warehouse or _default_pharmacy_warehouse(company, branch)
	if not patient or not sales_invoice:
		frappe.throw(_("Patient and Sales Invoice are required."))
	dispenses = []
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	for row in invoice.items:
		item_name = frappe.db.get_value("Item", {"item_code": row.item_code}, "name") or row.item_code
		md = frappe.get_doc({
			"doctype": "Healthcare Medication Dispense",
			"naming_series": "MDP-.#####",
			"patient": patient, "company": company, "branch": branch,
			"item": item_name, "qty": row.qty, "warehouse": warehouse,
			"status": "dispensed", "notes": _("Retail POS — {0}").format(sales_invoice),
		}).insert(ignore_permissions=True)
		dispenses.append(md.name)
	return {"ok": True, "dispenses": dispenses}

