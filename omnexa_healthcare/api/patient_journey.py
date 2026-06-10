# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Unified patient journey — registration through follow-up."""

from __future__ import annotations

import frappe
from frappe import _


JOURNEY_STEPS = [
	{"id": "registration", "label": "Registration", "doctype": "Healthcare Patient"},
	{"id": "booking", "label": "Online Booking", "page": "healthcare-booking"},
	{"id": "confirmation", "label": "Confirmation", "api": "notifications"},
	{"id": "check_in", "label": "Check-In", "doctype": "Healthcare Appointment"},
	{"id": "consultation", "label": "Consultation", "doctype": "Healthcare Encounter"},
	{"id": "investigation", "label": "Investigation", "doctype": "Healthcare Service Request"},
	{"id": "treatment", "label": "Treatment", "doctype": "Healthcare Procedure Order"},
	{"id": "billing", "label": "Billing", "doctype": "Healthcare Service Charge"},
	{"id": "follow_up", "label": "Follow-up", "doctype": "Healthcare Appointment"},
]


@frappe.whitelist()
def get_patient_journey(patient: str) -> dict:
	if not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient does not exist."), title=_("Patient"))
	steps = []
	for step in JOURNEY_STEPS:
		status = _step_status(patient, step)
		steps.append({**step, **status})
	completed = sum(1 for s in steps if s.get("state") == "completed")
	return {
		"patient": patient,
		"steps": steps,
		"progress_pct": round(completed / len(steps) * 100) if steps else 0,
		"friction_points": [s["id"] for s in steps if s.get("state") == "pending" and s["id"] in ("confirmation", "check_in")],
	}


def _step_status(patient: str, step: dict) -> dict:
	dt = step.get("doctype")
	if not dt:
		return {"state": "available", "count": 0}
	if dt == "Healthcare Patient":
		if frappe.db.exists(dt, patient):
			return {"state": "completed", "count": 1, "latest": patient}
		return {"state": "pending", "count": 0}
	if not frappe.get_meta(dt).has_field("patient"):
		return {"state": "available", "count": 0}
	count = frappe.db.count(dt, {"patient": patient})
	if count:
		latest = frappe.get_all(dt, filters={"patient": patient}, pluck="name", order_by="modified desc", limit=1)
		return {"state": "completed", "count": count, "latest": latest[0] if latest else None}
	return {"state": "pending", "count": 0}
