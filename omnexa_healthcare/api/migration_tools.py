# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Legacy EMR migration — bulk import patients and appointments."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def import_patients_bulk(rows: str | list) -> dict:
	data = frappe.parse_json(rows) if isinstance(rows, str) else rows
	if not isinstance(data, list):
		frappe.throw(_("rows must be a JSON list"))
	created, errors = [], []
	for idx, row in enumerate(data):
		try:
			name = row.get("patient_name") or row.get("name")
			if not name:
				raise ValueError("patient_name required")
			doc = frappe.get_doc(
				{
					"doctype": "Healthcare Patient",
					"patient_name": name,
					"gender": row.get("gender"),
					"birth_date": row.get("birth_date"),
					"mobile": row.get("mobile"),
					"company": row.get("company") or frappe.defaults.get_user_default("Company"),
					"branch": row.get("branch"),
				}
			).insert(ignore_permissions=True)
			created.append(doc.name)
		except Exception as exc:
			errors.append({"row": idx, "error": str(exc)})
	return {"created": len(created), "patients": created[:50], "errors": errors}


@frappe.whitelist()
def import_appointments_bulk(rows: str | list) -> dict:
	data = frappe.parse_json(rows) if isinstance(rows, str) else rows
	if not isinstance(data, list):
		frappe.throw(_("rows must be a JSON list"))
	created, errors = [], []
	for idx, row in enumerate(data):
		try:
			required = ("patient", "practitioner", "branch", "appointment_date")
			for key in required:
				if not row.get(key):
					raise ValueError(f"{key} required")
			doc = frappe.get_doc(
				{
					"doctype": "Healthcare Appointment",
					"patient": row["patient"],
					"practitioner": row["practitioner"],
					"branch": row["branch"],
					"specialty": row.get("specialty"),
					"appointment_date": getdate(row["appointment_date"]),
					"appointment_time": row.get("appointment_time") or "09:00:00",
					"status": row.get("status") or "Scheduled",
					"company": row.get("company") or frappe.db.get_value("Branch", row["branch"], "company"),
				}
			).insert(ignore_permissions=True)
			created.append(doc.name)
		except Exception as exc:
			errors.append({"row": idx, "error": str(exc)})
	return {"created": len(created), "appointments": created[:50], "errors": errors}
