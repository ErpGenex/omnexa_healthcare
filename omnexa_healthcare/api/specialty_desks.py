# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Specialty department desks — morgue, IPD beds, OT, dialysis, L&D, optometry."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today

from omnexa_healthcare.api.erp_desk_helpers import safe_doctype_fields


@frappe.whitelist()
def get_morgue_dashboard(branch: str | None = None, company: str | None = None) -> dict:
	if not frappe.db.exists("DocType", "Healthcare Morgue Case"):
		return {"cases": [], "open_count": 0, "missing_doctype": True}

	filters: dict = {}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	open_status = ["Admitted", "Stored", "Pending Release"]
	cases = frappe.get_all(
		"Healthcare Morgue Case",
		filters={**filters, "status": ["in", open_status]},
		fields=["name", "patient", "patient_display", "body_tag", "status", "intake_datetime", "branch", "storage_location"],
		order_by="intake_datetime desc",
		limit=50,
	)
	if not cases:
		cases = frappe.get_all(
			"Healthcare Morgue Case",
			filters=filters,
			fields=["name", "patient", "patient_display", "body_tag", "status", "intake_datetime", "branch", "storage_location"],
			order_by="modified desc",
			limit=20,
		)
	for row in cases:
		if not row.get("patient_display") and row.get("patient"):
			row["patient_name"] = frappe.db.get_value("Healthcare Patient", row.patient, "full_name") or ""
		else:
			row["patient_name"] = row.get("patient_display") or ""
	return {"cases": cases, "open_count": len([c for c in cases if c.get("status") in open_status])}


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


def _service_request_list_fields() -> list[str]:
	return [f for f in ["name", "patient", "request_title", "status", "authored_on"] if frappe.db.has_column("Healthcare Service Request", f)]


def _bed_list_fields() -> list[str]:
	return [f for f in ["name", "bed_label", "bed_type", "status", "service_unit", "ward_service_unit"] if frappe.db.has_column("Healthcare Bed", f)]


@frappe.whitelist()
def get_bed_board(branch: str, ward: str | None = None) -> dict:
	if not branch:
		frappe.throw(_("branch is required"))
	bed_filters = {"branch": branch}
	ward_field = "ward_service_unit" if frappe.db.has_column("Healthcare Bed", "ward_service_unit") else (
		"service_unit" if frappe.db.has_column("Healthcare Bed", "service_unit") else None
	)
	if ward and ward_field:
		bed_filters[ward_field] = ward
	beds = frappe.get_all(
		"Healthcare Bed",
		filters=bed_filters,
		fields=_bed_list_fields() or ["name", "bed_label", "status"],
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


def _dialysis_specialties() -> list[str]:
	specs = frappe.get_all(
		"Healthcare Specialty",
		filters={"specialty_name": ["like", "%Dialysis%"]},
		pluck="name",
		limit=5,
	)
	if not specs and frappe.db.has_column("Healthcare Specialty", "module_code"):
		specs = frappe.get_all("Healthcare Specialty", filters={"module_code": "dialysis"}, pluck="name", limit=5)
	return specs


def _ld_specialties() -> list[str]:
	specs = frappe.get_all(
		"Healthcare Specialty",
		filters={"specialty_name": ["like", "%Obstetric%"]},
		pluck="name",
		limit=5,
	)
	if not specs and frappe.db.has_column("Healthcare Specialty", "module_code"):
		specs = frappe.get_all("Healthcare Specialty", filters={"module_code": "neonatology"}, pluck="name", limit=5)
	return specs


@frappe.whitelist()
def get_dialysis_schedule(branch: str) -> list[dict]:
	"""Dialysis sessions from appointments in dialysis-related specialties."""
	specs = _dialysis_specialties()
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
	specs = _ld_specialties()
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
		fields=safe_doctype_fields(
			"Healthcare Diagnostic Report",
			["name", "report_title", "conclusion", "findings", "effective_datetime", "status", "pacs_wado_url"],
		),
		order_by="effective_datetime desc" if frappe.db.has_column("Healthcare Diagnostic Report", "effective_datetime") else "modified desc",
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
		fields=_service_request_list_fields() or ["name", "patient", "status"],
		order_by="modified desc",
		limit=30,
	) if frappe.db.exists("DocType", "Healthcare Service Request") else []
	for row in rows:
		row["order_date"] = row.get("authored_on") or row.get("modified") or ""
	return {"orders": rows, "count": len(rows)}


@frappe.whitelist()
def get_nutrition_orders(company: str | None = None, branch: str | None = None) -> dict:
	filters = {"branch": branch} if branch else {}
	rows = frappe.get_all(
		"Healthcare Service Request",
		filters={**filters, "request_category": ["in", ["nutrition", "dietetics", "Nutrition"]]},
		fields=_service_request_list_fields() or ["name", "patient", "status"],
		order_by="modified desc",
		limit=30,
	) if frappe.db.exists("DocType", "Healthcare Service Request") else []
	for row in rows:
		row["order_date"] = row.get("authored_on") or row.get("modified") or ""
	return {"orders": rows, "count": len(rows)}


@frappe.whitelist()
def get_appointments_directory(company: str | None = None, branch: str | None = None) -> dict:
	branch = branch or frappe.defaults.get_user_default("Branch")
	company = company or frappe.defaults.get_user_default("Company")
	from frappe.utils import add_days

	filters: dict = {"status": ["not in", ["Cancelled"]]}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	# Today + upcoming week so newly booked visits always appear
	window_start = f"{add_days(today(), -1)} 00:00:00"
	window_end = f"{add_days(today(), 14)} 23:59:59"
	filters["appointment_date"] = ["between", [window_start, window_end]]
	rows = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "appointment_date", "status", "specialty", "payment_status"],
		order_by="appointment_date desc",
		limit=100,
	)
	return {"appointments": rows, "count": len(rows)}


@frappe.whitelist()
def get_patients_directory(company: str | None = None, branch: str | None = None) -> dict:
	filters: dict = {}
	if company:
		filters["company"] = company
	if branch and frappe.db.has_column("Healthcare Patient", "branch"):
		filters["branch"] = branch
	fields = [f for f in ["name", "full_name", "gender", "birth_date"] if frappe.db.has_column("Healthcare Patient", f)]
	rows = frappe.get_all(
		"Healthcare Patient",
		filters=filters,
		fields=fields or ["name"],
		order_by="modified desc",
		limit=50,
	)
	for row in rows:
		row["mobile"] = frappe.db.get_value(
			"Healthcare Patient Telecom",
			{"parent": row.name, "parenttype": "Healthcare Patient"},
			"value",
			order_by="rank asc",
		) or ""
	return {"patients": rows, "count": len(rows)}

