# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""OPD queue / token board for front-desk and nursing."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, today


QUEUE_STATUSES = ("Scheduled", "Arrived", "In Consultation", "Completed", "No Show", "Cancelled")


@frappe.whitelist()
def api_get_patient_queue(
	branch: str,
	service_unit: str | None = None,
	queue_date: str | None = None,
) -> list[dict]:
	if not branch:
		frappe.throw(_("Branch is required"))

	queue_date = getdate(queue_date or today())
	filters = {
		"branch": branch,
		"appointment_date": ["between", [f"{queue_date} 00:00:00", f"{queue_date} 23:59:59"]],
		"status": ["in", ["Scheduled", "Arrived", "In Consultation"]],
	}
	if service_unit:
		filters["service_unit"] = service_unit

	rows = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=[
			"name",
			"patient",
			"patient_display",
			"practitioner",
			"specialty",
			"service_unit",
			"appointment_date",
			"slot_end",
			"status",
			"triage_level",
			"appointment_type",
		],
		order_by="triage_level asc, appointment_date asc",
		limit=200,
	)
	for row in rows:
		row["wait_mins"] = _wait_minutes(row.status, row.appointment_date)
	return rows


@frappe.whitelist()
def api_update_queue_status(appointment: str, status: str) -> dict:
	if not appointment:
		frappe.throw(_("Appointment is required"))
	status = (status or "").strip()
	if status not in QUEUE_STATUSES:
		frappe.throw(_("Invalid queue status: {0}").format(status))

	doc = frappe.get_doc("Healthcare Appointment", appointment)
	if not frappe.has_permission("Healthcare Appointment", "write", doc.name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc.status = status
	doc.save()
	return {"name": doc.name, "status": doc.status}


def _wait_minutes(status: str, appointment_date) -> int:
	if status not in ("Scheduled", "Arrived"):
		return 0
	start = frappe.utils.get_datetime(appointment_date)
	if not start:
		return 0
	delta = now_datetime() - start
	return max(0, int(delta.total_seconds() // 60))
