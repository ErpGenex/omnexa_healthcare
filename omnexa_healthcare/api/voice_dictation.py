# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Voice dictation — store transcript and structured clinical note."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def save_dictation(
	patient: str,
	transcript: str,
	encounter: str | None = None,
) -> dict:
	if not (patient and transcript):
		frappe.throw(_("patient and transcript are required"))
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	note = _structure_transcript(transcript)
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Voice Dictation",
			"patient": patient,
			"encounter": encounter,
			"dictated_by": frappe.session.user,
			"transcript": transcript,
			"structured_note": note,
			"status": "Draft",
			"company": company,
			"branch": branch,
		}
	).insert()
	return {"name": doc.name, "structured_note": note}


@frappe.whitelist()
def sign_dictation(name: str) -> dict:
	doc = frappe.get_doc("Healthcare Voice Dictation", name)
	if doc.dictated_by != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	doc.status = "Signed"
	doc.save()
	return {"name": doc.name, "status": doc.status}


def _structure_transcript(transcript: str) -> str:
	lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
	body = "<br>".join(frappe.utils.escape_html(ln) for ln in lines)
	return f"<p><strong>Dictated note</strong></p><p>{body}</p>"
