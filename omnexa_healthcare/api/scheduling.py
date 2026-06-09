# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.utils import flt, get_datetime

from omnexa_healthcare.scheduling_engine import (
	get_available_slots,
	get_practitioner_branches,
	validate_practitioner_appointment,
)


@frappe.whitelist()
def api_get_practitioner_branches(practitioner: str) -> list[dict]:
	if not practitioner:
		frappe.throw(_("Practitioner is required"))
	return get_practitioner_branches(practitioner)


@frappe.whitelist()
def api_get_available_slots(
	practitioner: str,
	branch: str,
	date: str,
	specialty: str | None = None,
) -> list[dict]:
	if not (practitioner and branch and date):
		frappe.throw(_("Practitioner, branch and date are required"))
	return get_available_slots(practitioner, branch, date, specialty=specialty)


@frappe.whitelist()
def api_book_appointment(payload: str | dict) -> dict:
	"""Create appointment from slot selection with fee preview."""
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	required = ("patient", "practitioner", "branch", "specialty", "appointment_date", "slot_end")
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key.replace("_", " ").title()))

	validate_practitioner_appointment(
		practitioner=data.practitioner,
		branch=data.branch,
		specialty=data.specialty,
		slot_start=data.appointment_date,
		slot_end=data.slot_end,
	)

	assignment = _pick_branch_assignment(data.practitioner, data.branch, data.specialty)
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Appointment",
			"naming_series": "HAP-.#####",
			"patient": data.patient,
			"company": data.company or frappe.db.get_value("Branch", data.branch, "company"),
			"branch": data.branch,
			"department": data.department or _default_department(data.branch),
			"service_unit": data.service_unit or assignment.get("service_unit"),
			"practitioner": data.practitioner,
			"specialty": data.specialty,
			"appointment_type": data.appointment_type or "Consultation",
			"appointment_date": get_datetime(data.appointment_date),
			"slot_end": get_datetime(data.slot_end),
			"booking_fee": flt(data.booking_fee) or flt(assignment.get("consultation_fee")),
			"payment_status": data.payment_status or "Unpaid",
			"status": "Scheduled",
		}
	)
	doc.insert()
	return {"name": doc.name, "booking_fee": doc.booking_fee}


def _pick_branch_assignment(practitioner: str, branch: str, specialty: str | None) -> dict:
	for row in get_practitioner_branches(practitioner):
		if row["branch"] == branch and (not specialty or row["specialty"] == specialty):
			return row
	return {}


def _default_department(branch: str) -> str | None:
	rows = frappe.get_all(
		"Healthcare Department",
		filters={"branch": branch, "docstatus": ["<", 2]},
		pluck="name",
		limit=1,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def api_get_practitioner_roster(branch: str | None = None, roster_date: str | None = None) -> list[dict]:
	"""Active practitioners with branch assignments and appointment load for a day."""
	from frappe.utils import getdate, today

	roster_date = getdate(roster_date or today())
	filters = {"status": "Active"}
	if branch:
		practitioner_names = frappe.db.sql(
			"""
			SELECT DISTINCT parent FROM `tabHealthcare Practitioner Branch Assignment`
			WHERE branch = %s AND is_active = 1
			""",
			branch,
		)
		filters["name"] = ["in", [r[0] for r in practitioner_names] or ["__none__"]]

	rows = []
	for pr in frappe.get_all(
		"Healthcare Practitioner",
		filters=filters,
		fields=["name", "practitioner_name", "license_number", "status"],
		order_by="practitioner_name asc",
	):
		doc = frappe.get_doc("Healthcare Practitioner", pr.name)
		branches = []
		for ba in doc.branch_assignments or []:
			if not ba.is_active or (branch and ba.branch != branch):
				continue
			branches.append(
				{
					"branch": ba.branch,
					"specialty": ba.specialty,
					"service_unit": ba.service_unit,
					"consultation_fee": ba.consultation_fee,
				}
			)
		appt_count = frappe.db.count(
			"Healthcare Appointment",
			{"practitioner": pr.name, "appointment_date": roster_date, "status": ["not in", ["Cancelled"]]},
		)
		rows.append(
			{
				**pr,
				"branches": branches,
				"appointment_count": appt_count,
				"roster_date": str(roster_date),
			}
		)
	return rows
