# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Ambient clinical documentation — session capture and draft note generation."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def start_ambient_session(patient: str, encounter: str | None = None, practitioner: str | None = None) -> dict:
	if not patient:
		frappe.throw(_("patient is required"))
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Ambient Session",
			"patient": patient,
			"encounter": encounter,
			"practitioner": practitioner,
			"status": "Recording",
			"company": company,
			"branch": branch,
		}
	).insert()
	return {"session": doc.name, "status": doc.status}


@frappe.whitelist()
def append_ambient_transcript(session: str, text: str) -> dict:
	doc = frappe.get_doc("Healthcare Ambient Session", session)
	doc.transcript = (doc.transcript or "") + "\n" + text.strip()
	doc.status = "Processing"
	doc.save()
	return {"session": doc.name, "length": len(doc.transcript or "")}


@frappe.whitelist()
def finalize_ambient_note(session: str) -> dict:
	doc = frappe.get_doc("Healthcare Ambient Session", session)
	transcript = (doc.transcript or "").strip()
	if not transcript:
		frappe.throw(_("Transcript is empty"))
	doc.draft_note = _generate_soap_draft(transcript, doc.patient)
	doc.status = "Review"
	doc.save()
	return {"session": doc.name, "draft_note": doc.draft_note, "status": doc.status}


def _generate_soap_draft(transcript: str, patient: str) -> str:
	patient_name = frappe.db.get_value("Healthcare Patient", patient, "full_name") or patient
	return f"""<h4>Subjective</h4>
<p>Patient {frappe.utils.escape_html(patient_name)} — ambient transcript captured {now_datetime()}.</p>
<blockquote>{frappe.utils.escape_html(transcript[:4000])}</blockquote>
<h4>Objective</h4>
<p><em>Review vitals and examination findings.</em></p>
<h4>Assessment</h4>
<p><em>AI-assisted — physician attestation required.</em></p>
<h4>Plan</h4>
<p><em>Confirm orders and follow-up.</em></p>"""
