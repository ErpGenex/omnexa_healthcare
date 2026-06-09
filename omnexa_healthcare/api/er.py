# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Emergency Department — registration, triage, board, disposition."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def register_er_visit(payload: str | dict) -> dict:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	required = ("patient", "company", "branch", "esi_level")
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Er Visit",
			"patient": data.patient,
			"company": data.company,
			"branch": data.branch,
			"arrival_datetime": data.get("arrival_datetime") or now_datetime(),
			"esi_level": str(data.esi_level),
			"chief_complaint": data.get("chief_complaint"),
			"track": data.get("track") or "Main",
			"status": "Registered",
		}
	).insert()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def update_er_status(name: str, status: str, disposition: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Er Visit", name)
	doc.status = status
	if disposition:
		doc.disposition = disposition
	if status == "In Treatment" and not doc.encounter:
		enc = frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": doc.patient,
				"company": doc.company,
				"branch": doc.branch,
				"status": "in-progress",
				"class": "emergency",
				"period_start": now_datetime(),
				"practitioner": doc.practitioner,
			}
		).insert(ignore_permissions=True)
		doc.encounter = enc.name
	doc.save()
	if status == "Disposition" and disposition == "Admit" and not doc.admission:
		from omnexa_healthcare.api.adt import create_admission_from_er

		doc.admission = create_admission_from_er(doc.name)
		doc.save()
	return {"name": doc.name, "status": doc.status, "encounter": doc.encounter, "admission": doc.admission}


@frappe.whitelist()
def api_get_er_board(branch: str, board_date: str | None = None) -> list[dict]:
	if not branch:
		frappe.throw(_("branch is required"))
	filters = {"branch": branch, "status": ["not in", ["Completed", "LWBS"]]}
	rows = frappe.get_all(
		"Healthcare Er Visit",
		filters=filters,
		fields=[
			"name",
			"patient",
			"arrival_datetime",
			"esi_level",
			"status",
			"track",
			"chief_complaint",
			"disposition",
		],
		order_by="esi_level asc, arrival_datetime asc",
		limit=200,
	)
	for row in rows:
		row["wait_mins"] = _wait_minutes(row.get("arrival_datetime"))
	return rows


def _wait_minutes(arrival) -> int:
	if not arrival:
		return 0
	from frappe.utils import time_diff_in_seconds

	return int(time_diff_in_seconds(now_datetime(), arrival) / 60)
