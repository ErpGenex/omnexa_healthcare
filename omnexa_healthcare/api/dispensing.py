# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Pharmacy dispensing bridge to Omnexa Accounting Stock Entry (Material Issue)."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime


@frappe.whitelist()
def create_stock_entry_from_medication_dispense(medication_dispense: str) -> dict:
	"""Create and submit a Material Issue Stock Entry for a Draft dispense; mark dispense as dispensed."""
	name = (medication_dispense or "").strip()
	if not name:
		frappe.throw(_("medication_dispense is required"))

	if not frappe.has_permission("Healthcare Medication Dispense", "write", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Healthcare Medication Dispense", name)
	if doc.status != "draft":
		frappe.throw(_("Only draft dispenses can post stock."), title=_("Status"))
	if doc.stock_entry:
		frappe.throw(_("Stock Entry already linked."), title=_("Stock Entry"))
	if not doc.warehouse:
		frappe.throw(_("Warehouse is required to issue stock."), title=_("Warehouse"))
	if not doc.item or flt(doc.qty) <= 0:
		frappe.throw(_("Item and a positive quantity are required."), title=_("Item"))

	item_doc = frappe.get_doc("Item", doc.item)
	if not item_doc.is_stock_item:
		frappe.throw(_("Item must be a stock item for inventory issue."), title=_("Item"))
	if flt(item_doc.current_stock_qty) < flt(doc.qty):
		frappe.throw(
			_("Insufficient stock (available: {0}).").format(flt(item_doc.current_stock_qty)),
			title=_("Stock"),
		)

	posting_date = getdate(doc.dispensed_datetime or now_datetime())

	se = frappe.new_doc("Stock Entry")
	se.company = doc.company
	se.branch = doc.branch
	se.posting_date = posting_date
	se.purpose = "Material Issue"
	se.from_warehouse = doc.warehouse
	se.remarks = _("Medication dispense {0} — patient {1}").format(doc.name, doc.patient)
	se.append(
		"items",
		{
			"item": doc.item,
			"item_code": item_doc.item_code,
			"qty": flt(doc.qty),
			"s_warehouse": doc.warehouse,
			"uom": item_doc.stock_uom,
			"rate": 0,
		},
	)

	se.insert()
	se.submit()

	doc.db_set("stock_entry", se.name, update_modified=False)
	doc.db_set("status", "dispensed", update_modified=False)
	doc.db_set("dispensed_datetime", doc.dispensed_datetime or now_datetime(), update_modified=False)

	return {"stock_entry": se.name, "medication_dispense": doc.name}
