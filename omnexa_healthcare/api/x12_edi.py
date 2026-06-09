# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""X12 EDI — 270/271 eligibility, 837 claim, 835 remittance."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


def _seg(*elements: str) -> str:
	return "*".join(str(e) for e in elements if e is not None) + "~"


@frappe.whitelist()
def build_x12_270(patient: str, payer: str, member_id: str | None = None) -> dict:
	if not (patient and payer):
		frappe.throw(_("patient and payer are required"))
	isa = _seg("ISA", "00", " " * 10, "00", " " * 10, "ZZ", "OMNEXA".ljust(15), "ZZ", payer[:15].ljust(15), now_datetime().strftime("%y%m%d"), "1200", "^", "00501", "000000001", "0", "P", ":")
	gs = _seg("GS", "HS", "OMNEXA", payer, now_datetime().strftime("%Y%m%d"), "1200", "1", "X", "005010X279A1")
	st = _seg("ST", "270", "0001", "005010X279A1")
	bht = _seg("BHT", "0022", "13", now_datetime().strftime("%Y%m%d"), "1200", "CH")
	payload = isa + gs + st + bht + _seg("HL", "1", "", "20", "1") + _seg("NM1", "PR", "2", payer) + _seg("HL", "2", "1", "21", "1") + _seg("NM1", "IL", "1", patient, "", "", "", "", "MI", member_id or "") + _seg("SE", "6", "0001") + _seg("GE", "1", "1") + _seg("IEA", "1", "000000001")
	return _store_x12("270", "Outbound", payload, patient=patient)


@frappe.whitelist()
def parse_x12_271(payload: str, patient: str | None = None) -> dict:
	eligible = "EB*1" in payload or "Eligible" in payload
	status = "Eligible" if eligible else "Not Eligible"
	return _store_x12("271", "Inbound", payload, patient=patient, extra={"eligible": eligible, "status": status})


@frappe.whitelist()
def build_x12_837(insurance_claim: str) -> dict:
	claim = frappe.get_doc("Healthcare Insurance Claim", insurance_claim)
	amt = flt(claim.claim_amount)
	isa = _seg("ISA", "00", " " * 10, "00", " " * 10, "ZZ", "OMNEXA".ljust(15), "ZZ", (claim.payer or "")[:15].ljust(15), now_datetime().strftime("%y%m%d"), "1200", "^", "00501", "000000002", "0", "P", ":")
	st = _seg("ST", "837", "0001", "005010X222A1")
	clm = _seg("CLM", claim.name, str(amt), "", "", "", "11:B:1", "Y", "A", "Y", "I")
	payload = isa + st + clm + _seg("SE", "3", "0001") + _seg("IEA", "1", "000000002")
	return _store_x12("837", "Outbound", payload, patient=claim.patient, insurance_claim=claim.name)


@frappe.whitelist()
def parse_x12_835(payload: str, insurance_claim: str | None = None) -> dict:
	paid = "0"
	for part in payload.split("~"):
		if part.startswith("CLP"):
			fields = part.split("*")
			if len(fields) > 4:
				paid = fields[4]
				break
	return _store_x12("835", "Inbound", payload, insurance_claim=insurance_claim, extra={"paid_amount": flt(paid)})


def _store_x12(
	transaction_type: str,
	direction: str,
	payload: str,
	patient: str | None = None,
	insurance_claim: str | None = None,
	extra: dict | None = None,
) -> dict:
	company = None
	branch = None
	if patient:
		company = frappe.db.get_value("Healthcare Patient", patient, "company")
		branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	elif insurance_claim:
		company = frappe.db.get_value("Healthcare Insurance Claim", insurance_claim, "company")
		branch = frappe.db.get_value("Healthcare Insurance Claim", insurance_claim, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare X12 Transaction",
			"transaction_type": transaction_type,
			"direction": direction,
			"patient": patient,
			"insurance_claim": insurance_claim,
			"payload": payload,
			"status": "Sent" if direction == "Outbound" else "Acknowledged",
			"company": company or frappe.defaults.get_user_default("Company"),
			"branch": branch,
		}
	).insert(ignore_permissions=True)
	out = {"transaction": doc.name, "transaction_type": transaction_type, "payload": payload}
	if extra:
		out.update(extra)
	return out
