# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Attach demo radiology preview URLs to existing diagnostic reports."""

from __future__ import annotations

import frappe

from omnexa_healthcare.utils.radiology_demo_catalog import DEMO_RAD_ROTATION, DEMO_RADIOLOGY_STUDIES


def upgrade_demo_radiology_reports(company: str | None = None, branch: str | None = None) -> dict:
	if not frappe.db.exists("DocType", "Healthcare Diagnostic Report"):
		return {"updated": 0}
	if not frappe.db.has_column("Healthcare Diagnostic Report", "pacs_wado_url"):
		return {"updated": 0}

	filters: dict = {"report_category": "radiology"}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch

	reports = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters=filters,
		fields=["name", "report_title", "pacs_wado_url"],
		order_by="creation asc",
		limit=200,
	)
	updated = 0
	for idx, row in enumerate(reports):
		if row.pacs_wado_url:
			continue
		study_key = DEMO_RAD_ROTATION[idx % len(DEMO_RAD_ROTATION)]
		study = DEMO_RADIOLOGY_STUDIES[study_key]
		values = {"pacs_wado_url": study["image"]}
		if frappe.db.has_column("Healthcare Diagnostic Report", "findings") and not frappe.db.get_value(
			"Healthcare Diagnostic Report", row.name, "findings"
		):
			values["findings"] = study["findings"]
		if frappe.db.has_column("Healthcare Diagnostic Report", "conclusion") and not frappe.db.get_value(
			"Healthcare Diagnostic Report", row.name, "conclusion"
		):
			values["conclusion"] = study["conclusion"]
		frappe.db.set_value("Healthcare Diagnostic Report", row.name, values, update_modified=False)
		updated += 1
	if updated:
		frappe.db.commit()
	return {"updated": updated}
