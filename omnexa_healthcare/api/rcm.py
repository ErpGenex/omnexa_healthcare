# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""RCM — prior authorization and claim remittance."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


@frappe.whitelist()
def submit_prior_authorization(name: str) -> dict:
	doc = frappe.get_doc("Healthcare Prior Authorization", name)
	doc.status = "Submitted"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_prior_authorization(name: str, auth_number: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Prior Authorization", name)
	doc.status = "Approved"
	if auth_number:
		doc.auth_number = auth_number
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def post_claim_remittance(payload: str | dict) -> dict:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	claim_name = data.get("insurance_claim")
	if not claim_name:
		frappe.throw(_("insurance_claim is required"))
	claim = frappe.get_doc("Healthcare Insurance Claim", claim_name)
	rem = frappe.get_doc(
		{
			"doctype": "Healthcare Claim Remittance",
			"insurance_claim": claim.name,
			"remittance_date": data.get("remittance_date") or now_datetime(),
			"paid_amount": flt(data.get("paid_amount")),
			"adjustment_amount": flt(data.get("adjustment_amount")),
			"reference_number": data.get("reference_number"),
			"company": claim.company,
			"branch": claim.branch,
		}
	).insert()
	paid = flt(data.get("paid_amount"))
	claim.approved_amount = paid
	if paid >= flt(claim.claim_amount):
		claim.mark_paid()
	else:
		claim.approve_claim(approved_amount=paid)
	return {"remittance": rem.name, "claim": claim.name, "status": claim.status}


@frappe.whitelist()
def submit_insurance_claim(name: str) -> dict:
	claim = frappe.get_doc("Healthcare Insurance Claim", name)
	claim.submit_claim()
	return {"name": claim.name, "status": claim.status}


@frappe.whitelist()
def approve_insurance_claim(name: str, approved_amount: float | None = None) -> dict:
	claim = frappe.get_doc("Healthcare Insurance Claim", name)
	claim.approve_claim(approved_amount=approved_amount)
	return {"name": claim.name, "status": claim.status, "approved_amount": claim.approved_amount}


@frappe.whitelist()
def split_billing(service_charge: str) -> dict:
	"""Split service charge into patient copay and insurer portion using coverage."""
	sc = frappe.get_doc("Healthcare Service Charge", service_charge)
	total = flt(getattr(sc, "total_amount", None))
	if not total:
		total = sum(flt(row.amount) for row in (sc.items or []))
	coverage = frappe.get_all(
		"Healthcare Patient Coverage",
		filters={"patient": sc.patient, "is_active": 1},
		fields=["name", "copay_percent", "insurance_plan"],
		limit=1,
	)
	if not coverage:
		return {"patient_portion": total, "insurer_portion": 0}
	copay_pct = flt(coverage[0].copay_percent) or 0
	patient_portion = total * copay_pct / 100
	return {"patient_portion": patient_portion, "insurer_portion": total - patient_portion, "coverage": coverage[0].name}
