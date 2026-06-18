# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Integrated Radiology desk — RIS + PACS + inventory + finance."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from omnexa_healthcare.api.erp_desk_helpers import (
	default_department_warehouse,
	get_accounts_summary,
	get_purchases_summary,
	get_stock_rows,
	resolve_company_branch,
	safe_doctype_fields,
)
from omnexa_healthcare.api.radiology import api_get_radiology_worklist


def _default_rad_warehouse(company: str) -> str | None:
	return default_department_warehouse(company, ["%Radiology%", "%RAD%", "%Imaging%", "DEMO-HC%"])


@frappe.whitelist()
def get_radiology_desk_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = resolve_company_branch(company, branch)
	warehouse = _default_rad_warehouse(company)
	today_date = getdate(today())

	report_filters: dict = {"report_category": "radiology"}
	if branch:
		report_filters["branch"] = branch

	under_reading = frappe.db.count(
		"Healthcare Diagnostic Report",
		{**report_filters, "status": ["in", ["registered", "preliminary", "partial"]]},
	)
	ready = frappe.db.count(
		"Healthcare Diagnostic Report",
		{**report_filters, "status": "final"},
	)
	today_scans = frappe.db.count(
		"Healthcare Service Request",
		{
			"branch": branch,
			"request_category": "imaging",
			"creation": [">=", f"{today_date} 00:00:00"],
		}
		if branch
		else {"request_category": "imaging", "creation": [">=", f"{today_date} 00:00:00"]},
	)
	total_scans = frappe.db.count(
		"Healthcare Service Request",
		{"branch": branch, "request_category": "imaging"} if branch else {"request_category": "imaging"},
	)

	modality_rows = frappe.db.sql(
		"""
		SELECT IFNULL(modality, request_title) AS modality, COUNT(*) AS cnt
		FROM `tabHealthcare Service Request`
		WHERE request_category = 'imaging'
		GROUP BY IFNULL(modality, request_title)
		ORDER BY cnt DESC
		LIMIT 6
		""",
		as_dict=True,
	)
	total_mod = sum(int(r.cnt) for r in modality_rows) or 1
	for row in modality_rows:
		row["pct"] = round(flt(row.cnt) / total_mod * 100, 1)

	worklist = api_get_radiology_worklist(branch or "") if branch else []
	upcoming = worklist[:12]

	recent_radiology_reports = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={**report_filters, "status": "final"},
		fields=safe_doctype_fields(
			"Healthcare Diagnostic Report",
			["name", "patient", "patient_display", "report_title", "pacs_wado_url", "findings", "effective_datetime"],
		),
		order_by="effective_datetime desc" if frappe.db.has_column("Healthcare Diagnostic Report", "effective_datetime") else "modified desc",
		limit=8,
	)

	devices = []
	if frappe.db.exists("DocType", "Healthcare Medical Device"):
		devices = frappe.get_all(
			"Healthcare Medical Device",
			filters={"company": company, "device_type": "Imaging Modality", "status": "Active"},
			fields=["name", "device_name", "status", "integration_protocol", "device_type"],
			limit=10,
		)
		for d in devices:
			d["modality"] = d.get("device_type") or d.get("integration_protocol")
	if not devices:
		devices = [
			{"device_name": "X-Ray 1", "status": "Available", "modality": "XR"},
			{"device_name": "CT Scanner", "status": "Working", "modality": "CT"},
			{"device_name": "MRI", "status": "Available", "modality": "MR"},
			{"device_name": "Ultrasound", "status": "Working", "modality": "US"},
		]

	return {
		"company": company,
		"branch": branch,
		"warehouse": warehouse,
		"kpis": {
			"under_reading": under_reading,
			"ready_reports": ready,
			"today_scans": today_scans,
			"total_scans": total_scans,
		},
		"modality_breakdown": modality_rows,
		"upcoming_orders": upcoming,
		"recent_radiology_reports": recent_radiology_reports,
		"worklist": worklist[:50],
		"devices": devices,
		"stock_rows": get_stock_rows(company, warehouse, "DEMO-HC-", 20),
		"accounts": get_accounts_summary(company, branch),
		"purchases": get_purchases_summary(company),
	}


@frappe.whitelist()
def schedule_radiology_order(service_request: str, appointment_date: str | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Service Request", service_request)
	doc.status = "active"
	if appointment_date and frappe.db.has_column("Healthcare Service Request", "occurrence_datetime"):
		doc.occurrence_datetime = appointment_date
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}
