# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Physician In Basket — results, signatures, tasks."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def api_get_in_basket(status: str = "Open") -> list[dict]:
	user = frappe.session.user
	return frappe.get_all(
		"Healthcare In Basket Item",
		filters={"recipient": user, "status": status},
		fields=["name", "item_type", "subject", "patient", "priority", "reference_doctype", "reference_name", "status"],
		order_by="priority desc, modified desc",
		limit=100,
	)


@frappe.whitelist()
def create_in_basket_item(
	recipient: str,
	item_type: str,
	subject: str,
	patient: str | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	priority: str = "Routine",
	company: str | None = None,
	branch: str | None = None,
) -> dict:
	company = company or frappe.defaults.get_user_default("Company")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare In Basket Item",
			"recipient": recipient,
			"item_type": item_type,
			"subject": subject,
			"patient": patient,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"priority": priority,
			"company": company,
			"branch": branch,
			"status": "Open",
		}
	).insert()
	return {"name": doc.name}


def notify_abnormal_diagnostic_report(doc, method=None):
	"""Create In Basket item for ordering physician when result is abnormal."""
	if not doc.get("abnormal_flag"):
		return
	recipient = doc.get("ordering_practitioner") or doc.get("practitioner")
	if not recipient:
		user = frappe.db.get_value("Healthcare Practitioner", {"user": ["is", "set"]}, "user")
		recipient = user or frappe.session.user
	if frappe.db.exists(
		"Healthcare In Basket Item",
		{
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"status": "Open",
		},
	):
		return
	frappe.get_doc(
		{
			"doctype": "Healthcare In Basket Item",
			"recipient": recipient,
			"item_type": "Critical",
			"subject": _("Abnormal result: {0}").format(doc.get("report_title") or doc.name),
			"patient": doc.get("patient"),
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"priority": "Urgent",
			"company": doc.get("company"),
			"branch": doc.get("branch"),
			"status": "Open",
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def complete_in_basket_item(name: str) -> dict:
	doc = frappe.get_doc("Healthcare In Basket Item", name)
	if doc.recipient != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	doc.status = "Done"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def request_cosign(name: str, cosigner: str) -> dict:
	"""Route signature item to attending for cosign."""
	doc = frappe.get_doc("Healthcare In Basket Item", name)
	if doc.item_type not in ("Signature", "Result"):
		frappe.throw(_("Item is not eligible for cosign"))
	cosign = create_in_basket_item(
		recipient=cosigner,
		item_type="Signature",
		subject=_("Cosign required: {0}").format(doc.subject),
		patient=doc.patient,
		reference_doctype=doc.reference_doctype,
		reference_name=doc.reference_name,
		priority="Urgent",
		company=doc.company,
		branch=doc.branch,
	)
	complete_in_basket_item(name)
	return {"original": name, "cosign_item": cosign["name"]}


@frappe.whitelist()
def process_refill_request(name: str, action: str) -> dict:
	"""Approve or deny pharmacy refill from In Basket."""
	if action not in ("approve", "deny"):
		frappe.throw(_("action must be approve or deny"))
	doc = frappe.get_doc("Healthcare In Basket Item", name)
	if doc.item_type != "Refill":
		frappe.throw(_("Not a refill request"))
	doc.status = "Done"
	doc.save()
	return {"name": doc.name, "action": action, "status": doc.status}
