# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Specialty department desks — morgue, IPD beds, OT, dialysis, L&D, optometry."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today


@frappe.whitelist()
def get_morgue_dashboard(branch: str | None = None, company: str | None = None) -> dict:
	filters: dict = {}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	open_status = ["Admitted", "admitted", "Stored", "stored", "Pending Release"]
	cases = frappe.get_all(
		"Healthcare Morgue Case",
		filters={**filters, "status": ["in", open_status]} if frappe.db.count("Healthcare Morgue Case", filters) else filters,
		fields=["name", "patient", "body_tag", "status", "intake_datetime", "branch"],
		order_by="intake_datetime desc",
		limit=50,
	)
	if not cases:
		cases = frappe.get_all(
			"Healthcare Morgue Case",
			filters=filters,
			fields=["name", "patient", "body_tag", "status", "intake_datetime", "branch"],
			order_by="modified desc",
			limit=20,
		)
	for row in cases:
		row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") if row.patient else ""
	return {"cases": cases, "open_count": len(cases)}


@frappe.whitelist()
def release_morgue_case(morgue_case: str, released_to: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Morgue Case", morgue_case)
	doc.status = "Released"
	if released_to and doc.meta.has_field("released_to"):
		doc.released_to = released_to
	if doc.meta.has_field("release_datetime"):
		doc.release_datetime = now_datetime()
	doc.save(ignore_permissions=True)
	return {"ok": True, "name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_bed_board(branch: str, ward: str | None = None) -> dict:
	if not branch:
		frappe.throw(_("branch is required"))
	bed_filters = {"branch": branch}
	if ward:
		bed_filters["ward_service_unit"] = ward
	beds = frappe.get_all(
		"Healthcare Bed",
		filters=bed_filters,
		fields=["name", "bed_label", "bed_type", "status", "ward_service_unit"],
		order_by="bed_label asc",
		limit=200,
	)
	census = {row.bed: row for row in frappe.db.sql(
		"""
		SELECT a.name AS admission, a.patient, a.bed, a.status AS admission_status
		FROM `tabHealthcare Admission` a
		WHERE a.branch = %s AND a.status IN ('admitted', 'Admitted', 'In Progress')
		""",
		branch,
		as_dict=True,
	)}
	for bed in beds:
		occ = census.get(bed.name)
		bed["occupied"] = bed.status in ("Occupied", "occupied") or bool(occ)
		bed["patient"] = occ.patient if occ else None
		bed["patient_name"] = (
			frappe.db.get_value("Healthcare Patient", occ.patient, "full_name") if occ and occ.patient else ""
		)
		bed["admission"] = occ.admission if occ else None
	return {"beds": beds, "occupied": sum(1 for b in beds if b.get("occupied")), "total": len(beds)}


@frappe.whitelist()
def discharge_admission(admission: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Admission", admission)
	doc.status = "discharged"
	if doc.meta.has_field("discharge_datetime"):
		doc.discharge_datetime = now_datetime()
	if reason and doc.meta.has_field("discharge_reason"):
		doc.discharge_reason = reason
	doc.save(ignore_permissions=True)
	if doc.bed:
		frappe.db.set_value("Healthcare Bed", doc.bed, "status", "Available", update_modified=False)
	return {"ok": True, "admission": doc.name, "status": doc.status}


@frappe.whitelist()
def get_ot_schedule(branch: str, schedule_date: str | None = None) -> list[dict]:
	date = getdate(schedule_date or today())
	filters = {"branch": branch}
	if frappe.db.has_column("Healthcare Surgical Case", "scheduled_start"):
		filters["scheduled_start"] = ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
	rows = frappe.get_all(
		"Healthcare Surgical Case",
		filters=filters,
		fields=["name", "patient", "procedure", "status", "scheduled_start", "operating_room"],
		order_by="scheduled_start asc",
		limit=50,
	)
	for row in rows:
		row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") or row.patient
	return rows


@frappe.whitelist()
def get_dialysis_schedule(branch: str) -> list[dict]:
	"""Dialysis sessions from appointments in dialysis-related specialties."""
	specs = frappe.get_all(
		"Healthcare Specialty",
		filters={"specialty_name": ["like", "%Dialysis%"]},
		pluck="name",
		limit=5,
	)
	if not specs:
		specs = frappe.get_all("Healthcare Specialty", filters={"module_code": "dialysis"}, pluck="name", limit=5)
	filters = {
		"branch": branch,
		"appointment_date": [">=", f"{today()} 00:00:00"],
		"status": ["not in", ["Cancelled", "No Show"]],
	}
	if specs:
		filters["specialty"] = ["in", specs]
	return frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "appointment_date", "status", "specialty"],
		order_by="appointment_date asc",
		limit=40,
	)


@frappe.whitelist()
def get_ld_board(branch: str) -> list[dict]:
	specs = frappe.get_all(
		"Healthcare Specialty",
		filters={"specialty_name": ["like", "%Obstetric%"]},
		pluck="name",
		limit=5,
	)
	if not specs:
		specs = frappe.get_all("Healthcare Specialty", filters={"module_code": "neonatology"}, pluck="name", limit=5)
	filters = {"branch": branch, "status": ["in", ["admitted", "Admitted"]]}
	if specs and frappe.db.has_column("Healthcare Admission", "specialty"):
		filters["specialty"] = ["in", specs]
	rows = frappe.get_all(
		"Healthcare Admission",
		filters=filters,
		fields=["name", "patient", "bed", "admission_datetime", "status"],
		order_by="admission_datetime desc",
		limit=30,
	)
	for row in rows:
		row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") or row.patient
	return rows


@frappe.whitelist()
def get_optometry_queue(branch: str) -> list[dict]:
	specs = frappe.get_all(
		"Healthcare Specialty",
		filters={"specialty_name": ["like", "%Ophthalm%"]},
		pluck="name",
		limit=5,
	)
	if not specs:
		specs = frappe.get_all("Healthcare Specialty", filters={"module_code": "ophthalmology"}, pluck="name", limit=5)
	filters = {
		"branch": branch,
		"appointment_date": [">=", f"{today()} 00:00:00"],
		"status": ["in", ["Scheduled", "Open", "In Progress"]],
	}
	if specs:
		filters["specialty"] = ["in", specs]
	rows = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "appointment_date", "status"],
		order_by="appointment_date asc",
		limit=40,
	)
	return rows


@frappe.whitelist()
def get_patient_results_portal(patient: str) -> dict:
	"""Lab + radiology results for patient consumer portal."""
	lab = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient, "report_category": "laboratory", "status": ["in", ["final", "preliminary"]]},
		fields=["name", "report_title", "conclusion", "effective_datetime", "status"],
		order_by="effective_datetime desc",
		limit=20,
	)
	rad = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient, "report_category": "radiology", "status": ["in", ["final", "preliminary"]]},
		fields=["name", "report_title", "conclusion", "findings", "effective_datetime", "status", "pacs_wado_url"],
		order_by="effective_datetime desc",
		limit=20,
	)
	return {"lab_results": lab, "radiology_results": rad}


@frappe.whitelist()
def get_ot_board(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	rows = get_ot_schedule(branch or "") if branch else []
	return {"cases": rows, "count": len(rows)}


@frappe.whitelist()
def get_dialysis_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	rows = get_dialysis_schedule(branch or "") if branch else []
	return {"sessions": rows, "count": len(rows)}


@frappe.whitelist()
def get_ld_board_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	rows = get_ld_board(branch or "") if branch else []
	return {"cases": rows, "count": len(rows)}


@frappe.whitelist()
def get_optometry_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	rows = get_optometry_queue(branch or "") if branch else []
	return {"orders": rows, "count": len(rows)}


@frappe.whitelist()
def get_blood_bank_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	from omnexa_healthcare.api.blood_bank import api_get_blood_bank_dashboard

	return api_get_blood_bank_dashboard(branch=branch, company=company)


@frappe.whitelist()
def get_rehab_orders(company: str | None = None, branch: str | None = None) -> dict:
	filters = {"branch": branch} if branch else {}
	rows = frappe.get_all(
		"Healthcare Service Request",
		filters={**filters, "request_category": ["in", ["physiotherapy", "rehabilitation", "Rehabilitation"]]},
		fields=["name", "patient", "request_title", "status", "order_date"],
		order_by="modified desc",
		limit=30,
	) if frappe.db.exists("DocType", "Healthcare Service Request") else []
	return {"orders": rows, "count": len(rows)}


@frappe.whitelist()
def get_nutrition_orders(company: str | None = None, branch: str | None = None) -> dict:
	filters = {"branch": branch} if branch else {}
	rows = frappe.get_all(
		"Healthcare Service Request",
		filters={**filters, "request_category": ["in", ["nutrition", "dietetics", "Nutrition"]]},
		fields=["name", "patient", "request_title", "status", "order_date"],
		order_by="modified desc",
		limit=30,
	) if frappe.db.exists("DocType", "Healthcare Service Request") else []
	return {"orders": rows, "count": len(rows)}


@frappe.whitelist()
def get_appointments_directory(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	filters: dict = {}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	rows = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "appointment_date", "status", "specialty"],
		order_by="appointment_date desc",
		limit=50,
	)
	return {"appointments": rows, "count": len(rows)}


@frappe.whitelist()
def get_patients_directory(company: str | None = None, branch: str | None = None) -> dict:
	filters: dict = {}
	if company:
		filters["company"] = company
	if branch and frappe.db.has_column("Healthcare Patient", "branch"):
		filters["branch"] = branch
	rows = frappe.get_all(
		"Healthcare Patient",
		filters=filters,
		fields=["name", "full_name", "mobile", "gender", "date_of_birth"],
		order_by="modified desc",
		limit=50,
	)
	return {"patients": rows, "count": len(rows)}

