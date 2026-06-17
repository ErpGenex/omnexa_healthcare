# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""GDPR patient erasure / anonymization workflow."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def create_erasure_request(patient: str, request_type: str = "Erasure", company: str | None = None, branch: str | None = None, notes: str | None = None) -> dict:
	if not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient not found."))
	company = company or frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = branch or frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Erasure Request",
			"patient": patient,
			"request_type": request_type,
			"status": "Submitted",
			"requested_by": frappe.session.user,
			"requested_on": now_datetime(),
			"notes": notes,
			"company": company,
			"branch": branch,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"ok": True, "name": doc.name}


@frappe.whitelist()
def execute_patient_erasure(request_name: str) -> dict:
	req = frappe.get_doc("Healthcare Patient Erasure Request", request_name)
	if req.request_type != "Erasure":
		frappe.throw(_("Only erasure requests can be executed via this method."))
	patient = req.patient
	_anonymize_patient(patient)
	req.db_set({"status": "Completed", "completed_on": now_datetime()})
	frappe.get_doc(
		{
			"doctype": "Healthcare Phi Access Log",
			"user": frappe.session.user,
			"patient": patient,
			"reference_doctype": "Healthcare Patient Erasure Request",
			"reference_name": req.name,
			"action": "Erasure",
		}
	).insert(ignore_permissions=True)
	return {"ok": True, "patient": patient, "request": req.name}


def _anonymize_patient(patient: str) -> None:
	"""Pseudonymize PHI fields — retain clinical statistics without identifiers."""
	tag = frappe.generate_hash(length=8)
	frappe.db.set_value(
		"Healthcare Patient",
		patient,
		{
			"given_name": "REDACTED",
			"family_name": tag,
			"patient_name": f"REDACTED-{tag}",
			"active": 0,
		},
	)
	for id_row in frappe.get_all("Healthcare Patient Identifier", filters={"parent": patient}, pluck="name"):
		frappe.db.set_value("Healthcare Patient Identifier", id_row, "value", f"ERASED-{tag}")


@frappe.whitelist()
def get_compliance_templates() -> dict:
	from omnexa_healthcare.compliance_docs import COMPLIANCE_DOCS

	return {
		"baa_template": {
			"title": "Business Associate Agreement (HIPAA)",
			"version": "2026.06",
			"body": "Standard BAA between covered entity and Omnexa Healthcare platform operator.",
		},
		"dpia_template": {
			"title": "Data Protection Impact Assessment (GDPR Art. 35)",
			"version": "2026.06",
			"body": "DPIA for multi-branch hospital PHI processing on Omnexa Healthcare.",
		},
		"isms_pack": {
			"title": "ISO 27001 ISMS Documentation Pack",
			"version": "2026.06",
			"sections": ["Scope", "Risk assessment", "Statement of Applicability", "Incident response"],
		},
		"iso27799_controls": {
			"title": "ISO 27799 Health Informatics Security Controls",
			"version": "2026.06",
			"sections": list(COMPLIANCE_DOCS.get("hipaa", {}).get("sections", {}).keys()),
		},
		"accounting_of_disclosures": {
			"title": "HIPAA Accounting of Disclosures",
			"query": "Healthcare Phi Access Log export by patient",
		},
	}
