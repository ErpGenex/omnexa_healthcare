# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Seed laboratory panels, reference ranges, and demo reports."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from omnexa_healthcare.utils.lab_demo_catalog import (
	LAB_DEMO_ORDER_ROTATION,
	LAB_DEMO_PANELS,
	demo_lab_result_rows,
	panel_request_title,
)


def ensure_lab_demo_catalog(company: str) -> dict:
	"""Create lab test panels and reference ranges for demo."""
	stats = {"panels": 0, "reference_ranges": 0}
	for panel_code, panel in LAB_DEMO_PANELS.items():
		if frappe.db.exists("Healthcare Lab Test Panel", panel_code):
			continue
		tests = []
		for section_en, _section_ar, section_tests in panel.get("sections") or []:
			for test_name, unit, low, high, _demo in section_tests:
				tests.append({"test_name": test_name, "unit": unit})
				_ensure_reference_range(company, test_name, low, high, stats)
		frappe.get_doc(
			{
				"doctype": "Healthcare Lab Test Panel",
				"panel_code": panel_code,
				"panel_name": panel.get("panel_name") or panel_code,
				"loinc_code": panel.get("loinc"),
				"company": company,
				"is_active": 1,
				"tests": tests,
			}
		).insert(ignore_permissions=True)
		stats["panels"] += 1
	return stats


def _ensure_reference_range(company: str, test_name: str, low, high, stats: dict) -> None:
	if frappe.db.exists("Healthcare Lab Reference Range", {"test_name": test_name, "company": company}):
		return
	frappe.get_doc(
		{
			"doctype": "Healthcare Lab Reference Range",
			"test_name": test_name,
			"company": company,
			"low_value": low,
			"high_value": high,
		}
	).insert(ignore_permissions=True)
	stats["reference_ranges"] += 1


def build_lab_report_payload(
	panel_code: str,
	patient: str,
	company: str,
	branch: str,
	service_request: str | None = None,
	encounter: str | None = None,
	status: str = "final",
) -> dict:
	rows = demo_lab_result_rows(panel_code, patient)
	abnormal = any(r.get("is_abnormal") for r in rows)
	return {
		"doctype": "Healthcare Diagnostic Report",
		"naming_series": "DGR-.#####",
		"patient": patient,
		"company": company,
		"branch": branch,
		"encounter": encounter,
		"based_on_service_request": service_request,
		"report_category": "laboratory",
		"report_title": panel_request_title(panel_code),
		"status": status,
		"effective_datetime": now_datetime(),
		"lab_panel": panel_code if frappe.db.exists("Healthcare Lab Test Panel", panel_code) else None,
		"lab_results": rows,
		"abnormal_flag": 1 if abnormal else 0,
		"conclusion": "Within normal limits (demo)." if not abnormal else "Some values require clinical correlation (demo).",
	}


def upgrade_demo_lab_reports(company: str, branch: str | None = None) -> int:
	"""Backfill structured lab result lines on existing laboratory reports."""
	ensure_lab_demo_catalog(company)
	filters: dict = {"company": company, "report_category": "laboratory"}
	if branch:
		filters["branch"] = branch
	reports = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters=filters,
		fields=["name", "patient", "lab_panel"],
		limit=500,
	)
	updated = 0
	for i, row in enumerate(reports):
		doc = frappe.get_doc("Healthcare Diagnostic Report", row.name)
		if doc.lab_results:
			continue
		panel_code = row.lab_panel or LAB_DEMO_ORDER_ROTATION[i % len(LAB_DEMO_ORDER_ROTATION)]
		doc.lab_results = []
		for line in demo_lab_result_rows(panel_code, row.patient):
			doc.append("lab_results", line)
		if not doc.lab_panel and frappe.db.exists("Healthcare Lab Test Panel", panel_code):
			doc.lab_panel = panel_code
		doc.save(ignore_permissions=True)
		updated += 1
	if updated:
		frappe.db.commit()
	return updated
