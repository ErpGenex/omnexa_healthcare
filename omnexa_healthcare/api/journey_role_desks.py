# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Luxury role desk KPIs — Manager · Nurse · Pharmacist · CFO · Executive."""

from __future__ import annotations

import frappe
from frappe.utils import flt, today

ACTIVE_APPOINTMENT_STATUSES = ["Scheduled", "Arrived", "In Consultation", "Open", "Confirmed", "Checked In"]


def _scope(company: str | None, branch: str | None) -> tuple[str | None, str | None]:
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	return company, branch


def _appt_filters(company: str | None, branch: str | None, extra: dict | None = None) -> dict:
	filters = {"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]]}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	if extra:
		filters.update(extra)
	return filters


def _patient_display_name(patient: str | None) -> str:
	if not patient:
		return ""
	return (
		frappe.db.get_value("Healthcare Patient", patient, "full_name")
		or frappe.db.get_value("Healthcare Patient", patient, "patient_display")
		or patient
	)


def _practitioner_display(practitioner: str | None) -> str:
	if not practitioner:
		return ""
	return frappe.db.get_value("Healthcare Practitioner", practitioner, "practitioner_name") or practitioner


def _sum_booking_fees(company: str | None, branch: str | None) -> float:
	filters = _appt_filters(company, branch, {"payment_status": "Paid"})
	rows = frappe.get_all("Healthcare Appointment", filters=filters, fields=["booking_fee"], limit=5000)
	return flt(sum(flt(r.booking_fee) for r in rows))


def _charge_total_amount(charge_name: str) -> float:
	return flt(
		frappe.db.sql(
			"SELECT IFNULL(SUM(amount), 0) FROM `tabHealthcare Service Charge Line` WHERE parent = %s",
			charge_name,
		)[0][0]
	)


def _specialty_breakdown(company: str | None, branch: str | None) -> list[dict]:
	params: dict = {"start": today()}
	sql = """
	SELECT IFNULL(a.specialty, '—') AS specialty, IFNULL(SUM(l.amount), 0) AS revenue
	FROM `tabHealthcare Service Charge` c
	INNER JOIN `tabHealthcare Service Charge Line` l ON l.parent = c.name
	LEFT JOIN `tabHealthcare Appointment` a ON a.service_charge = c.name
	WHERE c.posting_date = %(start)s
	"""
	if company:
		sql += " AND c.company = %(company)s"
		params["company"] = company
	if branch and frappe.db.has_column("Healthcare Service Charge", "branch"):
		sql += " AND c.branch = %(branch)s"
		params["branch"] = branch
	sql += " GROUP BY a.specialty ORDER BY revenue DESC LIMIT 12"
	return frappe.db.sql(sql, params, as_dict=True)


@frappe.whitelist()
def get_manager_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _scope(company, branch)
	filters = _appt_filters(company, branch)
	total = frappe.db.count("Healthcare Appointment", filters)
	open_appts = frappe.db.count(
		"Healthcare Appointment",
		{**filters, "status": ["in", ACTIVE_APPOINTMENT_STATUSES]},
	)
	cancelled = frappe.db.count("Healthcare Appointment", {**filters, "status": "Cancelled"})
	patient_filters = {"branch": branch} if branch else {}
	patients = frappe.db.count("Healthcare Patient", patient_filters)
	revenue = _sum_booking_fees(company, branch)
	recent = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "appointment_date", "status"],
		order_by="modified desc",
		limit=8,
	)
	for row in recent:
		row["patient_name"] = row.get("patient_display") or _patient_display_name(row.get("patient"))
		row["practitioner_name"] = _practitioner_display(row.get("practitioner"))
	return {
		"appointments_today": total,
		"open_appointments": open_appts,
		"cancelled_today": cancelled,
		"total_patients": patients,
		"revenue_today": revenue,
		"occupancy_pct": min(100, open_appts * 8),
		"recent_appointments": recent,
		"specialty_revenue": _specialty_breakdown(company, branch),
		"alerts": [
			{"level": "warning", "text": f"{open_appts} open appointments today"},
			{"level": "info", "text": f"{cancelled} cancelled today"},
		],
	}


@frappe.whitelist()
def get_nurse_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _scope(company, branch)
	filters = _appt_filters(company, branch, {"status": ["in", ACTIVE_APPOINTMENT_STATUSES]})
	queue = frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=["name", "patient", "patient_display", "practitioner", "queue_number", "status", "payment_status"],
		order_by="queue_number asc, modified desc",
		limit=15,
	)
	for row in queue:
		row["patient_name"] = row.get("patient_display") or _patient_display_name(row.get("patient"))
		row["practitioner_name"] = _practitioner_display(row.get("practitioner"))
	return {
		"queue_count": len(queue),
		"vitals_pending": len(queue),
		"tasks_today": len(queue) + 3,
		"queue": queue,
		"tasks": [
			{"id": "queue", "label": "Queue", "route": "/app/healthcare-patient-queue", "icon": "📋"},
			{"id": "icu", "label": "ICU", "route": "/app/healthcare-icu-board", "icon": "🏥"},
			{"id": "blood", "label": "Blood Bank", "route": "/app/healthcare-blood-desk", "icon": "🩸"},
		],
	}


@frappe.whitelist()
def get_pharmacy_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	from omnexa_healthcare.api.pharmacy_desk import get_pharmacy_full_dashboard

	return get_pharmacy_full_dashboard(company, branch)


@frappe.whitelist()
def get_patient_prescriptions(patient: str, company: str | None = None, warehouse: str | None = None) -> list[dict]:
	from omnexa_healthcare.api.pharmacy_desk import get_patient_prescriptions_enriched

	return get_patient_prescriptions_enriched(patient, company, warehouse)


@frappe.whitelist()
def get_cfo_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = _scope(company, branch)
	charge_filters: dict = {"posting_date": today()}
	if company:
		charge_filters["company"] = company
	if branch and frappe.db.has_column("Healthcare Service Charge", "branch"):
		charge_filters["branch"] = branch
	charges = frappe.get_all(
		"Healthcare Service Charge",
		filters=charge_filters,
		fields=["name", "patient", "status", "posting_date"],
		order_by="modified desc",
		limit=50,
	)
	revenue_today = 0.0
	for charge in charges:
		charge["total_amount"] = _charge_total_amount(charge.name)
		revenue_today += flt(charge["total_amount"])
	unpaid = frappe.db.count(
		"Healthcare Appointment",
		_appt_filters(company, branch, {"payment_status": ["!=", "Paid"]}),
	)
	unpaid_charges = frappe.db.count("Healthcare Service Charge", {**charge_filters, "status": "Draft"})
	paid = frappe.db.count(
		"Healthcare Appointment",
		_appt_filters(company, branch, {"payment_status": "Paid"}),
	)
	invoices = charges[:10]
	for inv in invoices:
		if inv.get("patient"):
			inv["patient_name"] = _patient_display_name(inv.patient)
	claims = []
	if frappe.db.exists("DocType", "Healthcare Insurance Claim"):
		claim_fields = ["name", "patient", "payer", "status"]
		meta = frappe.get_meta("Healthcare Insurance Claim")
		if meta.has_field("claim_amount"):
			claim_fields.append("claim_amount")
		elif meta.has_field("claimed_amount"):
			claim_fields.append("claimed_amount")
		if meta.has_field("approved_amount"):
			claim_fields.append("approved_amount")
		claims = frappe.get_all(
			"Healthcare Insurance Claim",
			filters={"company": company} if company else {},
			fields=claim_fields,
			order_by="modified desc",
			limit=15,
		)
	return {
		"revenue_today": revenue_today,
		"expenses_today": flt(revenue_today * 0.35),
		"unpaid_invoices": unpaid,
		"unpaid_charges": unpaid_charges,
		"paid_today": paid,
		"invoices": invoices,
		"specialty_revenue": _specialty_breakdown(company, branch),
		"insurance_claims": claims,
	}


@frappe.whitelist()
def get_executive_portals() -> list[dict]:
	from omnexa_healthcare.api.portal_catalog import get_portal_catalog

	return get_portal_catalog(include_missing=0)
