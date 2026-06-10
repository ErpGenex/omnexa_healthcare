# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Companion lodging — check-in/out linked to inpatient admission."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def register_companion_stay(payload: str | dict) -> dict:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	required = ("patient", "admission", "companion_name", "bed", "company", "branch")
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Companion Stay",
			"patient": data.patient,
			"admission": data.admission,
			"companion_name": data.companion_name,
			"relationship": data.get("relationship") or "Other",
			"companion_phone": data.get("companion_phone"),
			"companion_id_number": data.get("companion_id_number"),
			"bed": data.bed,
			"check_in_datetime": data.get("check_in_datetime") or now_datetime(),
			"status": "active",
			"company": data.company,
			"branch": data.branch,
			"notes": data.get("notes"),
		}
	).insert()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def discharge_companion_stay(name: str) -> dict:
	doc = frappe.get_doc("Healthcare Companion Stay", name)
	doc.status = "discharged"
	doc.check_out_datetime = now_datetime()
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def api_get_companion_board(branch: str) -> list[dict]:
	if not branch:
		frappe.throw(_("branch is required"))
	return frappe.db.sql(
		"""
		SELECT
			c.name, c.companion_name, c.relationship, c.patient, c.admission,
			c.bed, c.check_in_datetime, c.status,
			b.bed_label, a.patient_display
		FROM `tabHealthcare Companion Stay` c
		LEFT JOIN `tabHealthcare Bed` b ON b.name = c.bed
		LEFT JOIN `tabHealthcare Admission` a ON a.name = c.admission
		WHERE c.branch = %s AND c.status = 'active'
		ORDER BY c.check_in_datetime DESC
		LIMIT 200
		""",
		branch,
		as_dict=True,
	)
