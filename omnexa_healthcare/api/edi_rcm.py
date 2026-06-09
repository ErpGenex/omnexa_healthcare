# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""EDI / NPHIES / X12-style eligibility and claim bundles."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


@frappe.whitelist()
def check_eligibility(patient: str, payer: str, member_id: str | None = None) -> dict:
	if not (patient and payer):
		frappe.throw(_("patient and payer are required"))
	coverage = frappe.get_all(
		"Healthcare Patient Coverage",
		filters={"patient": patient, "payer": payer, "is_active": 1},
		fields=["name", "copay_percent", "insurance_plan"],
		limit=1,
	)
	status = "Eligible" if coverage else "Unknown"
	copay = flt(coverage[0].copay_percent) if coverage else 0
	payload = {
		"patient": patient,
		"payer": payer,
		"member_id": member_id,
		"eligible": status == "Eligible",
		"copay_percent": copay,
		"checked_at": str(now_datetime()),
		"standard": "FHIR CoverageEligibilityResponse",
	}
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Eligibility Check",
			"patient": patient,
			"payer": payer,
			"member_id": member_id,
			"status": status,
			"copay_percent": copay,
			"response_payload": json.dumps(payload),
			"company": company,
			"branch": branch,
		}
	).insert(ignore_permissions=True)
	return {"eligibility_check": doc.name, **payload}


@frappe.whitelist()
def build_nphies_claim_bundle(insurance_claim: str) -> dict:
	claim = frappe.get_doc("Healthcare Insurance Claim", insurance_claim)
	bundle = {
		"resourceType": "Bundle",
		"type": "transaction",
		"timestamp": str(now_datetime()),
		"entry": [
			{
				"resource": {
					"resourceType": "Claim",
					"id": claim.name,
					"status": "active",
					"patient": {"reference": f"Patient/{claim.patient}"},
					"insurer": {"reference": f"Organization/{claim.payer}"},
					"total": {"value": flt(claim.claim_amount), "currency": frappe.db.get_default("currency") or "USD"},
				}
			}
		],
	}
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Nphies Claim Bundle",
			"insurance_claim": claim.name,
			"bundle_type": "Claim",
			"status": "Draft",
			"fhir_bundle": json.dumps(bundle, indent=2),
			"company": claim.company,
			"branch": claim.branch,
		}
	).insert(ignore_permissions=True)
	return {"bundle": doc.name, "fhir": bundle}
