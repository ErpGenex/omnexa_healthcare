# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Bridge to Omnexa Accounting Sales Invoice for hospital billing."""

import frappe
from frappe import _
from frappe.utils import flt, getdate


@frappe.whitelist()
def create_sales_invoice_from_service_charge(service_charge: str) -> dict:
	"""Create and submit a Sales Invoice from a Draft Healthcare Service Charge."""
	service_charge = (service_charge or "").strip()
	if not service_charge:
		frappe.throw(_("service_charge is required"))

	if not frappe.has_permission("Healthcare Service Charge", "write", service_charge):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Healthcare Service Charge", service_charge)
	if doc.status != "Draft":
		frappe.throw(_("Only Draft service charges can be invoiced."), title=_("Status"))
	if doc.sales_invoice:
		frappe.throw(_("Sales Invoice already created."), title=_("Sales Invoice"))
	if not doc.items:
		frappe.throw(_("Add at least one line item."), title=_("Items"))

	currency = frappe.db.get_value("Company", doc.company, "default_currency")
	if not currency:
		frappe.throw(_("Set default currency on Company."), title=_("Company"))

	si = frappe.new_doc("Sales Invoice")
	si.company = doc.company
	si.branch = doc.branch
	si.customer = doc.billing_customer
	si.posting_date = getdate(doc.posting_date)
	si.currency = currency
	si.conversion_rate = 1.0

	for row in doc.items:
		if not row.item:
			frappe.throw(_("Row {0}: Item is required.").format(row.idx), title=_("Items"))
		si.append(
			"items",
			{
				"item": row.item,
				"item_code": row.item_code,
				"qty": flt(row.qty),
				"rate": flt(row.rate),
			},
		)

	si.insert()
	si.submit()

	doc.db_set("sales_invoice", si.name, update_modified=False)
	doc.db_set("status", "Invoiced", update_modified=False)

	try:
		from omnexa_healthcare.api.physician_compensation_engine import accrue_from_service_charge

		accrue_from_service_charge(doc.name, sales_invoice=si.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "physician_compensation_accrual")

	return {"name": si.name, "status": doc.status}
