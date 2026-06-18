# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Sync Omnexa Lab Report print format from bundled HTML."""

from __future__ import annotations

from pathlib import Path

import frappe

PRINT_NAME = "Omnexa Lab Report"
DOC_TYPE = "Healthcare Diagnostic Report"
HTML_PATH = (
	Path(__file__).resolve().parents[2]
	/ "omnexa_healthcare"
	/ "print_format"
	/ "omnexa_lab_report"
	/ "omnexa_lab_report.html"
)


def execute():
	html = HTML_PATH.read_text(encoding="utf-8")
	if frappe.db.exists("Print Format", PRINT_NAME):
		frappe.db.set_value(
			"Print Format",
			PRINT_NAME,
			{
				"html": html,
				"doc_type": DOC_TYPE,
				"custom_format": 1,
				"print_format_type": "Jinja",
				"disabled": 0,
				"default_print_language": "ar",
			},
			update_modified=True,
		)
	else:
		frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": PRINT_NAME,
				"doc_type": DOC_TYPE,
				"module": "Omnexa Healthcare",
				"custom_format": 1,
				"print_format_type": "Jinja",
				"standard": "Yes",
				"disabled": 0,
				"default_print_language": "ar",
				"html": html,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()

	company = frappe.db.get_single_value("Global Defaults", "default_company")
	if company:
		from omnexa_healthcare.utils.lab_demo_seed import ensure_lab_demo_catalog, upgrade_demo_lab_reports

		ensure_lab_demo_catalog(company)
		branch = frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc")
		upgrade_demo_lab_reports(company, branch)
