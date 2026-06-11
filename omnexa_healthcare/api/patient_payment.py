# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Online patient payment checkout."""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.utils import flt, get_url, now_datetime


def _payments_enabled() -> bool:
	return bool(frappe.db.get_single_value("Healthcare Settings", "enable_online_patient_payments"))


def _build_checkout_url(checkout_name: str) -> str:
	token = hashlib.sha256(f"{checkout_name}-{frappe.local.site}".encode()).hexdigest()[:24]
	return get_url(f"/api/method/omnexa_healthcare.api.patient_payment.payment_checkout_page?checkout={checkout_name}&token={token}")


@frappe.whitelist()
def create_payment_checkout(patient: str, amount: float, company: str, service_charge: str | None = None, branch: str | None = None) -> dict:
	if not _payments_enabled():
		frappe.throw(_("Online payments are disabled."), title=_("Payment"))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Payment Checkout",
			"patient": patient,
			"amount": flt(amount),
			"service_charge": service_charge,
			"company": company,
			"branch": branch,
			"status": "Pending",
		}
	)
	doc.insert(ignore_permissions=True)
	checkout_url = _build_checkout_url(doc.name)
	frappe.db.set_value("Healthcare Patient Payment Checkout", doc.name, "checkout_url", checkout_url, update_modified=False)
	gateway = frappe.db.get_single_value("Healthcare Settings", "payment_gateway") or "Manual"
	return {
		"ok": True,
		"checkout": doc.name,
		"amount": doc.amount,
		"checkout_url": checkout_url,
		"gateway": gateway,
		"status": doc.status,
	}


@frappe.whitelist()
def confirm_payment(checkout: str, payment_reference: str) -> dict:
	doc = frappe.get_doc("Healthcare Patient Payment Checkout", checkout)
	if doc.status == "Paid":
		return {"ok": True, "checkout": doc.name, "status": doc.status, "already_paid": True}
	doc.payment_reference = payment_reference
	doc.status = "Paid"
	doc.save(ignore_permissions=True)
	if doc.service_charge:
		try:
			frappe.db.set_value("Healthcare Service Charge", doc.service_charge, "status", "Paid", update_modified=True)
		except Exception:
			pass
	return {"ok": True, "checkout": doc.name, "status": doc.status, "paid_at": now_datetime()}


@frappe.whitelist(allow_guest=True)
def payment_checkout_page(checkout: str, token: str | None = None) -> dict:
	"""Guest-safe checkout status for patient payment journey."""
	if not frappe.db.exists("Healthcare Patient Payment Checkout", checkout):
		frappe.throw(_("Checkout not found."), title=_("Payment"))
	doc = frappe.get_doc("Healthcare Patient Payment Checkout", checkout)
	return {
		"checkout": doc.name,
		"patient": doc.patient,
		"amount": doc.amount,
		"status": doc.status,
		"gateway": frappe.db.get_single_value("Healthcare Settings", "payment_gateway") or "Manual",
	}
