# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Integrated Laboratory desk — LIS + inventory + finance."""

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
)
from omnexa_healthcare.api.inventory_healthcare import get_par_level_alerts
from omnexa_healthcare.api.lab_lis import api_generate_specimen_barcode, api_get_lab_worklist


def _default_lab_warehouse(company: str) -> str | None:
	return default_department_warehouse(company, ["%Lab WH%", "%LABORATORY%", "%Lab%", "DEMO-HC%"])


@frappe.whitelist()
def get_lab_desk_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company, branch = resolve_company_branch(company, branch)
	warehouse = _default_lab_warehouse(company)
	today_date = getdate(today())

	sample_filters = {"company": company}
	if branch:
		sample_filters["branch"] = branch

	in_progress = frappe.db.count(
		"Healthcare Lab Sample",
		{**sample_filters, "status": ["in", ["planned", "collected", "in_lab"]]},
	)
	ready = frappe.db.count(
		"Healthcare Diagnostic Report",
		{
			**({"branch": branch} if branch else {}),
			"report_category": "laboratory",
			"status": ["in", ["final", "preliminary"]],
		},
	)
	today_samples = frappe.db.count(
		"Healthcare Lab Sample",
		{**sample_filters, "creation": [">=", f"{today_date} 00:00:00"]},
	)
	total_samples = frappe.db.count("Healthcare Lab Sample", sample_filters)

	top_tests = frappe.db.sql(
		"""
		SELECT report_title AS test_name, COUNT(*) AS cnt
		FROM `tabHealthcare Diagnostic Report`
		WHERE report_category = 'laboratory'
		GROUP BY report_title
		ORDER BY cnt DESC
		LIMIT 8
		""",
		as_dict=True,
	)
	total_top = sum(int(r.cnt) for r in top_tests) or 1
	for row in top_tests:
		row["pct"] = round(flt(row.cnt) / total_top * 100, 1)

	worklist = api_get_lab_worklist(branch or "") if branch else []
	recent = worklist[:12] if worklist else frappe.get_all(
		"Healthcare Lab Sample",
		filters=sample_filters,
		fields=["name", "patient_display", "sample_type", "status", "specimen_id", "collected_datetime"],
		order_by="modified desc",
		limit=12,
	)

	devices = []
	if frappe.db.exists("DocType", "Healthcare Medical Device"):
		devices = frappe.get_all(
			"Healthcare Medical Device",
			filters={"company": company, "device_type": "Lab Analyzer", "status": "Active"},
			fields=["name", "device_name", "status", "integration_protocol", "device_type"],
			limit=10,
		)
		for d in devices:
			d["modality"] = d.get("device_type") or d.get("integration_protocol")

	recent_reports = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={
			**({"branch": branch} if branch else {}),
			"report_category": "laboratory",
		},
		fields=["name", "patient_display", "report_title", "status", "effective_datetime"],
		order_by="modified desc",
		limit=12,
	)

	return {
		"company": company,
		"branch": branch,
		"warehouse": warehouse,
		"kpis": {
			"in_progress": in_progress,
			"ready_results": ready,
			"today_tests": today_samples,
			"total_tests": total_samples,
		},
		"top_tests": top_tests,
		"recent_samples": recent,
		"recent_lab_reports": recent_reports,
		"lab_print_format": "Omnexa Lab Report",
		"worklist": worklist[:50],
		"stock_rows": get_stock_rows(company, warehouse, "DEMO-HC-", 25),
		"par_alerts": get_par_level_alerts(company=company, branch=branch)[:15] if branch else [],
		"devices": devices,
		"accounts": get_accounts_summary(company, branch),
		"purchases": get_purchases_summary(company),
	}


@frappe.whitelist()
def get_lab_print_format() -> str:
	return "Omnexa Lab Report"


@frappe.whitelist()
def collect_lab_sample(lab_sample: str) -> dict:
	doc = frappe.get_doc("Healthcare Lab Sample", lab_sample)
	if doc.status == "planned":
		doc.status = "collected"
		doc.save(ignore_permissions=True)
	return api_generate_specimen_barcode(lab_sample)


@frappe.whitelist()
def finalize_lab_report(diagnostic_report: str) -> dict:
	doc = frappe.get_doc("Healthcare Diagnostic Report", diagnostic_report)
	doc.status = "final"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}
