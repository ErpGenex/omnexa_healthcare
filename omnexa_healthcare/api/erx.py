# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Global ePrescription — create · sign · verify · QR · smart drug search."""

from __future__ import annotations

import hashlib
import json
import hmac

import frappe
from frappe import _
from frappe.utils import now_datetime, today

from omnexa_healthcare.api.cds import evaluate_erx_cds


def _sign_payload(payload: dict) -> str:
	secret = frappe.get_site_config().get("secret_key") or frappe.local.conf.get("secret_key") or "omnexa-erx"
	raw = json.dumps(payload, sort_keys=True, default=str)
	return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def _make_qr_token(medication_request: str, patient: str) -> str:
	payload = {"mr": medication_request, "patient": patient, "ts": str(now_datetime())}
	sig = _sign_payload(payload)
	return f"{medication_request}.{sig[:32]}"


@frappe.whitelist()
def search_drugs(query: str = "", limit: int = 20) -> list[dict]:
	limit = min(int(limit or 20), 100)
	if not query:
		return frappe.get_all(
			"Healthcare Drug Formulary",
			filters={"is_active": 1},
			fields=["formulary_code", "drug_name", "generic_name", "rxnorm_code", "strength", "dosage_form", "is_controlled"],
			limit=limit,
			order_by="drug_name asc",
		)
	q = query.strip()
	rows = frappe.get_all(
		"Healthcare Rxnorm Code",
		filters={"is_active": 1, "drug_name": ["like", f"%{q}%"]},
		fields=["rxnorm_cui", "drug_name", "generic_name", "strength", "dosage_form"],
		limit=limit,
	)
	if not rows:
		rows = frappe.get_all(
			"Healthcare Rxnorm Code",
			filters={"is_active": 1, "generic_name": ["like", f"%{q}%"]},
			fields=["rxnorm_cui", "drug_name", "generic_name", "strength", "dosage_form"],
			limit=limit,
		)
	return rows


@frappe.whitelist()
def create_medication_request(
	patient: str,
	practitioner: str,
	company: str,
	branch: str,
	diagnosis: str,
	items: str | list,
	encounter: str | None = None,
	icd10_code: str | None = None,
	icd11_code: str | None = None,
) -> dict:
	if isinstance(items, str):
		items = json.loads(items)
	if not items:
		frappe.throw(_("At least one medication line is required."))
	cds_alerts = evaluate_erx_cds(patient, items)
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Medication Request",
			"patient": patient,
			"practitioner": practitioner,
			"encounter": encounter,
			"diagnosis": diagnosis,
			"icd10_code": icd10_code,
			"icd11_code": icd11_code,
			"status": "Draft",
			"company": company,
			"branch": branch,
			"items": items,
		}
	)
	doc.insert(ignore_permissions=True)
	_log_cds_alerts(doc, cds_alerts)
	return {"ok": True, "name": doc.name, "cds_alerts": cds_alerts}


def _log_cds_alerts(doc, alerts: list[dict]) -> None:
	for alert in alerts:
		frappe.get_doc(
			{
				"doctype": "Healthcare Cds Alert Log",
				"medication_request": doc.name,
				"patient": doc.patient,
				"check_type": alert.get("check_type") or "Other",
				"severity": alert.get("severity") or "Warning",
				"message": alert.get("message") or alert.get("description") or "",
				"company": doc.company,
				"branch": doc.branch,
			}
		).insert(ignore_permissions=True)


@frappe.whitelist()
def sign_medication_request(name: str, override_reasons: str | dict | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Medication Request", name)
	if doc.docstatus == 1:
		return {"ok": True, "name": doc.name, "already_signed": True}
	if doc.status == "Cancelled":
		frappe.throw(_("Cannot sign a cancelled prescription."))
	overrides = frappe.parse_json(override_reasons) if isinstance(override_reasons, str) else (override_reasons or {})
	unresolved = frappe.get_all(
		"Healthcare Cds Alert Log",
		filters={"medication_request": name, "overridden": 0, "severity": ["in", ["Critical", "Contraindicated"]]},
		pluck="name",
	)
	if unresolved and not overrides:
		frappe.throw(_("Critical CDS alerts must be overridden before signing."), title=_("CDS"))
	for alert_name in unresolved:
		frappe.db.set_value(
			"Healthcare Cds Alert Log",
			alert_name,
			{"overridden": 1, "override_reason": overrides.get(alert_name) or _("Clinician override at sign"), "overridden_by": frappe.session.user},
		)
	payload = {
		"medication_request": doc.name,
		"patient": doc.patient,
		"practitioner": doc.practitioner,
		"diagnosis": doc.diagnosis,
		"items": [row.as_dict() for row in doc.items],
		"signed_on": str(now_datetime()),
	}
	sig_hash = _sign_payload(payload)
	doc.signature_hash = sig_hash
	doc.qr_token = _make_qr_token(doc.name, doc.patient)
	doc.signed_on = now_datetime()
	doc.signed_by = frappe.session.user
	doc.save(ignore_permissions=True)
	doc.submit()
	frappe.get_doc(
		{
			"doctype": "Healthcare Prescription Signature",
			"medication_request": doc.name,
			"signed_by": frappe.session.user,
			"signed_on": now_datetime(),
			"signature_hash": sig_hash,
			"payload_json": json.dumps(payload, default=str),
		}
	).insert(ignore_permissions=True)
	return {"ok": True, "name": doc.name, "signature_hash": sig_hash, "qr_token": doc.qr_token}


@frappe.whitelist()
def cancel_medication_request(name: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Medication Request", name)
	if doc.docstatus == 1:
		doc.cancel()
	doc.db_set("status", "Cancelled")
	return {"ok": True, "name": doc.name, "reason": reason}


@frappe.whitelist()
def verify_qr_token(qr_token: str) -> dict:
	if not qr_token or "." not in qr_token:
		frappe.throw(_("Invalid QR token."))
	mr_name = qr_token.split(".", 1)[0]
	if not frappe.db.exists("Healthcare Medication Request", mr_name):
		frappe.throw(_("Prescription not found."))
	doc = frappe.get_doc("Healthcare Medication Request", mr_name)
	if doc.qr_token != qr_token:
		frappe.throw(_("QR signature mismatch — prescription may be forged."), title=_("Verify"))
	return {
		"valid": True,
		"medication_request": doc.name,
		"patient": doc.patient,
		"practitioner": doc.practitioner,
		"status": doc.status,
		"signed_on": doc.signed_on,
		"items": [row.as_dict() for row in doc.items],
	}


@frappe.whitelist()
def pharmacy_verify_and_dispense(
	medication_request: str,
	warehouse: str,
	substitutions: str | list | None = None,
) -> dict:
	doc = frappe.get_doc("Healthcare Medication Request", medication_request)
	if doc.docstatus != 1:
		frappe.throw(_("Prescription must be submitted before pharmacy verification."))
	if doc.status not in ("Signed", "Dispensed"):
		frappe.throw(_("Prescription must be signed before pharmacy verification."))
	if isinstance(substitutions, str):
		substitutions = json.loads(substitutions) if substitutions else []
	for sub in substitutions or []:
		frappe.get_doc(
			{
				"doctype": "Healthcare Pharmacy Substitution Log",
				"medication_request": doc.name,
				"original_drug": sub.get("original_drug"),
				"substituted_drug": sub.get("substituted_drug"),
				"reason": sub.get("reason") or "Generic",
				"pharmacist": frappe.session.user,
				"company": doc.company,
				"branch": doc.branch,
				"notes": sub.get("notes"),
			}
		).insert(ignore_permissions=True)
	dispenses = []
	for row in doc.items:
		item_code = row.formulary_item or row.rxnorm_code or row.drug_name
		from omnexa_healthcare.api.pharmacy import api_pharmacy_pos_dispense

		out = api_pharmacy_pos_dispense(doc.patient, item_code, row.quantity or 1, warehouse, doc.branch, doc.company)
		dispenses.append(out.get("medication_dispense"))
	doc.db_set(
		{
			"status": "Dispensed",
			"verified_by_pharmacist": frappe.session.user,
			"verified_on": now_datetime(),
			"dispense_reference": dispenses[0] if dispenses else None,
		}
	)
	return {"ok": True, "medication_request": doc.name, "dispenses": dispenses}


@frappe.whitelist()
def list_patient_prescriptions(patient: str, limit: int = 20) -> list[dict]:
	limit = min(int(limit or 20), 100)
	return frappe.get_all(
		"Healthcare Medication Request",
		filters={"patient": patient, "docstatus": ["!=", 2]},
		fields=["name", "status", "diagnosis", "signed_on", "practitioner", "qr_token"],
		limit=limit,
		order_by="creation desc",
	)


@frappe.whitelist()
def export_erx_pdf(medication_request: str) -> dict:
	doc = frappe.get_doc("Healthcare Medication Request", medication_request)
	html = frappe.get_print("Healthcare Medication Request", doc.name)
	return {"html": html, "medication_request": doc.name, "qr_token": doc.qr_token}


@frappe.whitelist()
def schedule_refill_reminders(days_ahead: int = 7) -> dict:
	"""Adherence — flag signed Rx nearing end of duration."""
	days_ahead = int(days_ahead or 7)
	reminders = []
	for doc in frappe.get_all(
		"Healthcare Medication Request",
		filters={"status": "Signed", "docstatus": 1},
		fields=["name", "patient"],
		limit=200,
	):
		full = frappe.get_doc("Healthcare Medication Request", doc.name)
		for row in full.items or []:
			if not row.duration_days:
				continue
			end = frappe.utils.add_days(full.signed_on.date() if full.signed_on else today(), row.duration_days)
			if end <= frappe.utils.add_days(today(), days_ahead):
				reminders.append({"medication_request": doc.name, "patient": doc.patient, "drug": row.drug_name, "refill_due": str(end)})
	return {"count": len(reminders), "reminders": reminders}
