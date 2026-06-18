# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Pharmacy desk — POS, inventory, purchases, stock transfers."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, today

from omnexa_healthcare.api.erp_desk_helpers import get_accounts_summary, get_purchases_summary
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


def _item_selling_rate(item: str) -> float:
	code = _item_code(item)
	if not code:
		return 0.0
	if frappe.db.has_column("Item", "standard_selling_rate"):
		std = frappe.db.get_value("Item", item, "standard_selling_rate")
		if std and flt(std) > 0:
			return flt(std)
	if frappe.db.has_column("Item", "standard_rate"):
		std = frappe.db.get_value("Item", item, "standard_rate")
		if std and flt(std) > 0:
			return flt(std)
	rate = frappe.db.sql(
		"""
		SELECT rate FROM `tabSales Invoice Item`
		WHERE item_code = %s AND rate > 0
		ORDER BY modified DESC LIMIT 1
		""",
		(code,),
	)
	return flt(rate[0][0]) if rate else 0.0


def _demo_pharmacy_rate(item_code: str) -> float:
	try:
		from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER, PHARMACY_ITEMS

		code = (item_code or "").upper()
		if not code.startswith(DEMO_MARKER):
			return 0.0
		for short, _label, rate in PHARMACY_ITEMS:
			if code == f"{DEMO_MARKER}{short}":
				return flt(rate)
	except Exception:
		return 0.0
	return 0.0


def _item_rate(item: str) -> float:
	rate = _item_selling_rate(item)
	if rate > 0:
		return rate
	return _demo_pharmacy_rate(_item_code(item))


def _resolve_item_name(item_ref: str) -> str:
	item_ref = (item_ref or "").strip()
	if not item_ref:
		return ""
	if frappe.db.exists("Item", item_ref):
		return item_ref
	return frappe.db.get_value("Item", {"item_code": item_ref}, "name") or item_ref


def _ensure_batch_no(item: str, batch_no: str | None = None) -> str | None:
	if not cint(frappe.db.get_value("Item", item, "has_batch_no")):
		return None
	batch_no = (batch_no or "").strip()
	if not batch_no:
		code = (_item_code(item) or "ITEM").replace(" ", "-")[:18]
		batch_no = f"PH-{getdate(today()):%Y%m%d}-{code}-{frappe.generate_hash(length=4)}"
	if not frappe.db.exists("Batch", batch_no):
		frappe.get_doc({"doctype": "Batch", "batch_id": batch_no, "item": item}).insert(ignore_permissions=True)
	return batch_no


def _ensure_serial_nos(item: str, qty: float, serial_no: str | None = None) -> str | None:
	if not cint(frappe.db.get_value("Item", item, "has_serial_no")):
		return None
	if serial_no and str(serial_no).strip():
		return str(serial_no).strip()
	item_code = _item_code(item)
	serials: list[str] = []
	for _ in range(max(cint(qty), 1)):
		sn = f"PH-{frappe.generate_hash(length=10)}"
		if not frappe.db.exists("Serial No", sn):
			frappe.get_doc({"doctype": "Serial No", "serial_no": sn, "item_code": item_code}).insert(
				ignore_permissions=True
			)
		serials.append(sn)
	return "\n".join(serials)


def _stock_entry_item_row(item: str, line: dict, **warehouse_fields) -> dict:
	item_doc = frappe.get_doc("Item", item)
	row = {
		"item": item,
		"item_code": item_doc.item_code,
		"qty": flt(line.get("qty")),
		"uom": item_doc.stock_uom,
		**warehouse_fields,
	}
	batch = _ensure_batch_no(item, line.get("batch_no"))
	if batch:
		row["batch_no"] = batch
	serial = _ensure_serial_nos(item, line.get("qty"), line.get("serial_no"))
	if serial:
		row["serial_no"] = serial
	rate = flt(line.get("rate"))
	if rate:
		if frappe.get_meta("Stock Entry Item").has_field("rate"):
			row["rate"] = rate
		elif frappe.get_meta("Stock Entry Item").has_field("basic_rate"):
			row["basic_rate"] = rate
	return row


def _normalize_drug_text(value: str) -> str:
	import re

	return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _resolve_item_for_medication(medication_text: str, company: str) -> dict | None:
	text = (medication_text or "").strip().lower()
	if not text:
		return None
	norm_text = _normalize_drug_text(text)

	if frappe.db.has_column("Healthcare Drug Formulary", "default_item"):
		for row in frappe.get_all(
			"Healthcare Drug Formulary",
			filters={"is_active": 1},
			fields=["drug_name", "generic_name", "default_item", "formulary_code"],
			limit=200,
		):
			for token in (row.drug_name, row.generic_name):
				if token and (token.lower() in text or _normalize_drug_text(token) in norm_text) and row.default_item:
					return {
						"item": row.default_item,
						"item_code": _item_code(row.default_item),
						"label": row.drug_name,
						"rate": _item_rate(row.default_item),
						"source": "formulary",
					}

	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER, PHARMACY_ITEMS

	for code, label, rate in PHARMACY_ITEMS:
		if label.lower() in text or code.lower() in text or _normalize_drug_text(label) in norm_text:
			item_code = f"{DEMO_MARKER}{code}"
			item_name = frappe.db.get_value("Item", {"item_code": item_code, "company": company}, "name")
			if item_name:
				return {
					"item": item_name,
					"item_code": item_code,
					"label": label,
						"rate": rate or _item_rate(item_name),
					"source": "demo_item",
				}
	return None


def ensure_pharmacy_pos_items(company: str | None = None) -> dict:
	"""Enable healthcare demo pharmacy items for embedded Retail POS."""
	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER, PHARMACY_ITEMS

	company = (company or "").strip() or frappe.defaults.get_user_default("Company") or ""
	if not company:
		return {"enabled": 0}
	enabled = 0
	item_codes = [f"{DEMO_MARKER}{code}" for code, _, _ in PHARMACY_ITEMS]
	has_pos_field = frappe.db.has_column("Item", "show_in_retail_pos")
	has_product_type = frappe.db.has_column("Item", "product_type")
	for item_code in item_codes:
		row = frappe.db.get_value(
			"Item",
			{"item_code": item_code, "company": company},
			["name", "show_in_retail_pos", "is_sales_item", "product_type"],
			as_dict=True,
		)
		if not row:
			continue
		values: dict = {}
		if has_pos_field and not cint(row.show_in_retail_pos):
			values["show_in_retail_pos"] = 1
		if not cint(row.is_sales_item):
			values["is_sales_item"] = 1
		if has_product_type and not row.product_type:
			values["product_type"] = "Consumable"
		if values:
			frappe.db.set_value("Item", row.name, values, update_modified=False)
			enabled += 1
	if enabled:
		frappe.db.commit()
	return {"enabled": enabled, "company": company}


@frappe.whitelist()
def get_pharmacy_full_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	ensure_pharmacy_pos_items(company)
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
	filters: dict = {"company": company, "disabled": 0}
	if frappe.db.has_column("Item", "is_sales_item"):
		filters["is_sales_item"] = 1
	elif frappe.db.has_column("Item", "is_stock_item"):
		filters["is_stock_item"] = 1
	if frappe.db.has_column("Item", "show_in_retail_pos"):
		filters["show_in_retail_pos"] = 1
	if q:
		filters["item_name"] = ["like", f"%{q}%"]
	else:
		from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER

		filters["item_code"] = ["like", f"{DEMO_MARKER}%"]
	fields = ["name", "item_code", "item_name"]
	if frappe.db.has_column("Item", "current_stock_qty"):
		fields.append("current_stock_qty")
	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=fields,
		order_by="item_name asc",
		limit=limit,
	)
	for row in rows:
		row["on_hand"] = _warehouse_qty(row.name, warehouse) if warehouse else flt(row.get("current_stock_qty"))
		row["rate"] = _item_rate(row.name)
	return rows


@frappe.whitelist()
def get_patient_prescriptions_enriched(patient: str, company: str | None = None, warehouse: str | None = None) -> list[dict]:
	company, branch = _resolve_company_branch(company, None)
	warehouse = warehouse or _default_pharmacy_warehouse(company, branch)
	rows = frappe.get_all(
		"Healthcare Medication Statement",
		filters={"patient": patient, "status": ["in", ["active", "Active", "draft", "Draft", "on-hold", "On Hold"]]},
		fields=["name", "medication_text", "dosage_text", "status", "encounter", "modified"],
		order_by="modified desc",
		limit=20,
	)
	for row in rows:
		resolved = _resolve_item_for_medication(row.medication_text, company)
		row["resolved_item"] = resolved.get("item") if resolved else None
		row["resolved_item_code"] = resolved.get("item_code") if resolved else None
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
		rate = flt(line.get("rate") or _item_rate(item))
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
		item = _resolve_item_name(line.get("item"))
		qty = flt(line.get("qty"))
		rate = flt(line.get("rate"))
		if not item or qty <= 0:
			continue
		se.append(
			"items",
			_stock_entry_item_row(item, line, t_warehouse=warehouse),
		)

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
		item = _resolve_item_name(line.get("item"))
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
		se.append(
			"items",
			_stock_entry_item_row(
				item,
				line,
				s_warehouse=source_warehouse,
				t_warehouse=target_warehouse,
			),
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
def check_pharmacy_dispense_cds(patient: str, lines: str | list | None = None) -> dict:
	"""Clinical decision support — drug interactions for cart lines."""
	if not patient:
		return {"alerts": []}
	raw = lines
	if isinstance(raw, str):
		raw = json.loads(raw) if raw.strip().startswith("[") else []
	if not isinstance(raw, list):
		raw = []
	seen: set[str] = set()
	alerts: list[dict] = []
	for row in raw:
		item = (row or {}).get("item") or (row or {}).get("item_code")
		if not item or item in seen:
			continue
		seen.add(item)
		for alert in api_check_drug_interactions(patient, item) or []:
			alerts.append(
				{
					"severity": alert.get("severity") or "Info",
					"message": alert.get("message") or alert.get("description") or str(alert),
				}
			)
	return {"alerts": alerts}


@frappe.whitelist()
def get_pharmacy_accounts_summary(company: str | None = None, branch: str | None = None, limit: int = 15) -> dict:
	company, branch = _resolve_company_branch(company, branch)
	return get_accounts_summary(company, branch, limit)


@frappe.whitelist()
def get_pharmacy_purchases_summary(company: str | None = None, branch: str | None = None, limit: int = 15) -> dict:
	company, _branch = _resolve_company_branch(company, branch)
	limit = min(int(limit or 15), 50)
	base = get_purchases_summary(company, limit)
	purchase_receipts: list[dict] = []
	if frappe.db.exists("DocType", "Purchase Receipt"):
		filters: dict = {"company": company}
		if _branch and frappe.db.has_column("Purchase Receipt", "branch"):
			filters["branch"] = _branch
		pr_fields = ["name", "supplier", "posting_date", "grand_total", "docstatus"]
		if frappe.db.has_column("Purchase Receipt", "status"):
			pr_fields.append("status")
		purchase_receipts = frappe.get_all(
			"Purchase Receipt",
			filters=filters,
			fields=pr_fields,
			order_by="modified desc",
			limit=limit,
		)
		for row in purchase_receipts:
			if "status" not in row and row.get("docstatus") is not None:
				row["status"] = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(cint(row.docstatus), row.docstatus)
	return {
		"purchase_orders": base.get("purchase_orders") or [],
		"purchase_receipts": purchase_receipts,
		"material_receipts": [
			row
			for row in (base.get("stock_entries") or [])
			if (row.get("purpose") or "") in ("Material Receipt", "Purchase Receipt", "Receive")
		]
		or base.get("stock_entries")
		or [],
	}


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

