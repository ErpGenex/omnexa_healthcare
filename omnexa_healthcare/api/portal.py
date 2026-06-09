# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Patient portal registration and self-service APIs."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import random_string


@frappe.whitelist(allow_guest=True)
def register_portal_patient(payload: str | dict) -> dict:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	required = ("given_name", "family_name", "email", "company", "branch")
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key.replace("_", " ").title()))

	user = frappe.db.get_value("User", {"email": data.email})
	if user:
		frappe.throw(_("An account with this email already exists."))

	patient = frappe.get_doc(
		{
			"doctype": "Healthcare Patient",
			"naming_series": "HP-.#####",
			"given_name": data.given_name,
			"family_name": data.family_name,
			"company": data.company,
			"branch": data.branch,
			"active": 1,
			"telecom": [{"system": "email", "value": data.email, "use": "home"}],
		}
	).insert(ignore_permissions=True)

	portal_user = frappe.get_doc(
		{
			"doctype": "User",
			"email": data.email,
			"first_name": data.given_name,
			"last_name": data.family_name,
			"send_welcome_email": 0,
			"user_type": "Website User",
		}
	).insert(ignore_permissions=True)
	portal_user.add_roles("Patient Portal User" if frappe.db.exists("Role", "Patient Portal User") else "Customer")

	return {"patient": patient.name, "user": portal_user.name}


@frappe.whitelist()
def get_my_appointments(patient: str) -> list[dict]:
	if not patient:
		frappe.throw(_("patient is required"))
	return frappe.get_all(
		"Healthcare Appointment",
		filters={"patient": patient},
		fields=["name", "appointment_date", "status", "practitioner", "specialty", "branch"],
		order_by="appointment_date desc",
		limit=50,
	)


@frappe.whitelist()
def patient_mobile_home(patient: str) -> dict:
	if not patient:
		frappe.throw(_("patient is required"))
	return {
		"appointments": get_my_appointments(patient),
		"lab_results": get_my_lab_results(patient),
		"imaging_results": get_my_imaging_results(patient),
		"medications": frappe.get_all(
			"Healthcare Medication Statement",
			filters={"patient": patient, "status": "active"},
			fields=["medication_text", "dosage_text", "status"],
			limit=20,
		),
	}


@frappe.whitelist()
def get_my_lab_results(patient: str) -> list[dict]:
	if not patient:
		frappe.throw(_("patient is required"))
	return frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient, "report_category": "laboratory"},
		fields=["name", "report_title", "status", "effective_datetime", "abnormal_flag"],
		order_by="effective_datetime desc",
		limit=30,
	)


@frappe.whitelist()
def get_my_imaging_results(patient: str) -> list[dict]:
	if not patient:
		frappe.throw(_("patient is required"))
	return frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient, "report_category": "radiology"},
		fields=["name", "report_title", "status", "effective_datetime", "pacs_wado_url"],
		order_by="effective_datetime desc",
		limit=30,
	)


@frappe.whitelist()
def queue_patient_notification(patient: str, message: str, channel: str = "Push") -> dict:
	if not (patient and message):
		frappe.throw(_("patient and message are required"))
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Push Notification",
			"patient": patient,
			"channel": channel,
			"message": message,
			"status": "Queued",
			"company": company,
		}
	).insert(ignore_permissions=True)
	return {"notification": doc.name, "status": doc.status}
