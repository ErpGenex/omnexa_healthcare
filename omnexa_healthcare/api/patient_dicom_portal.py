# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Patient-facing DICOM / imaging study access."""

from __future__ import annotations

import frappe


@frappe.whitelist()
def get_my_imaging_study_urls(patient: str) -> list[dict]:
	"""Return imaging results with WADO viewer links for patient portal."""
	reports = frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient, "docstatus": ["!=", 2]},
		fields=["name", "report_date", "modality", "status", "study_instance_uid"],
		order_by="report_date desc",
		limit_page_length=50,
	)
	wado_base = frappe.db.get_single_value("Healthcare Settings", "pacs_wado_base_url") or ""
	secondary = frappe.db.get_value("Healthcare Pacs Endpoint", {"role": "Secondary", "is_active": 1}, "base_url")
	base = secondary or wado_base
	out: list[dict] = []
	for row in reports:
		viewer_url = None
		if base and row.study_instance_uid:
			viewer_url = f"{base.rstrip('/')}/studies/{row.study_instance_uid}"
		out.append(
			{
				"report": row.name,
				"report_date": row.report_date,
				"modality": row.modality,
				"status": row.status,
				"study_instance_uid": row.study_instance_uid,
				"viewer_url": viewer_url,
				"dicom_viewer_page": "/app/healthcare-dicom-viewer",
			}
		)
	return out
