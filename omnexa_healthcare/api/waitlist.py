# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Appointment waitlist for patients."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def join_appointment_waitlist(patient: str, practitioner: str, company: str, branch: str, specialty: str | None = None, preferred_date: str | None = None, priority: str = "Normal") -> dict:
	if not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient not found."), title=_("Waitlist"))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Appointment Waitlist",
			"patient": patient,
			"practitioner": practitioner,
			"specialty": specialty,
			"preferred_date": preferred_date,
			"priority": priority,
			"status": "Waiting",
			"company": company,
			"branch": branch,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "waitlist": doc.name, "status": doc.status}


@frappe.whitelist()
def list_waitlist(patient: str | None = None, practitioner: str | None = None, status: str = "Waiting") -> list[dict]:
	filters: dict = {}
	if patient:
		filters["patient"] = patient
	if practitioner:
		filters["practitioner"] = practitioner
	if status:
		filters["status"] = status
	return frappe.get_all(
		"Healthcare Appointment Waitlist",
		filters=filters,
		fields=["name", "patient", "practitioner", "specialty", "preferred_date", "priority", "status", "appointment"],
		order_by="priority desc, creation asc",
	)


@frappe.whitelist()
def notify_waitlist_slot(practitioner: str, appointment_date: str, company: str, branch: str) -> dict:
	"""Notify first waiting patient and link when appointment is created."""
	rows = frappe.get_all(
		"Healthcare Appointment Waitlist",
		filters={"practitioner": practitioner, "status": "Waiting", "company": company, "branch": branch},
		fields=["name", "patient"],
		order_by="priority desc, creation asc",
		limit_page_length=1,
	)
	row = rows[0] if rows else None
	if not row:
		return {"notified": False, "reason": "no_waitlist"}
	frappe.db.set_value("Healthcare Appointment Waitlist", row.name, "status", "Notified", update_modified=True)
	try:
		from omnexa_healthcare.api.patient_notifications import queue_patient_notification

		queue_patient_notification(row.patient, f"Appointment slot available on {appointment_date}", channel="SMS")
	except Exception:
		pass
	return {"notified": True, "waitlist": row.name, "patient": row.patient}
