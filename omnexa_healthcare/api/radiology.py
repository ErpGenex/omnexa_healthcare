# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""RIS — radiology worklist and structured reporting."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def api_get_radiology_worklist(branch: str, modality: str | None = None) -> list[dict]:
	if not branch:
		frappe.throw(_("Branch is required"))
	filters = {"branch": branch, "request_category": "imaging", "status": ["not in", ["completed", "cancelled", "revoked"]]}
	if modality:
		filters["modality"] = modality
	return frappe.get_all(
		"Healthcare Service Request",
		filters=filters,
		fields=["name", "patient", "patient_display", "request_title", "modality", "priority", "status", "authored_on"],
		order_by="priority asc, authored_on asc",
		limit=200,
	)


@frappe.whitelist()
def api_create_radiology_report_from_template(service_request: str, template: str) -> dict:
	sr = frappe.get_doc("Healthcare Service Request", service_request)
	tpl = frappe.get_doc("Healthcare Radiology Report Template", template)
	report = frappe.get_doc(
		{
			"doctype": "Healthcare Diagnostic Report",
			"naming_series": "DGR-.#####",
			"patient": sr.patient,
			"company": sr.company,
			"branch": sr.branch,
			"encounter": sr.encounter,
			"based_on_service_request": sr.name,
			"report_category": "radiology",
			"report_title": sr.request_title,
			"status": "preliminary",
			"effective_datetime": now_datetime(),
			"findings": tpl.structured_body,
			"structured_template": template,
			"pacs_wado_url": _pacs_url(sr),
		}
	).insert(ignore_permissions=True)
	sr.db_set("status", "completed", update_modified=False)
	return {"diagnostic_report": report.name}


def _pacs_url(sr) -> str | None:
	base = frappe.db.get_single_value("Healthcare Settings", "pacs_wado_base_url")
	if not base:
		return None
	return f"{base.rstrip('/')}/studies?patient={sr.patient}&accession={sr.name}"


@frappe.whitelist()
def api_get_dicom_viewer_config(diagnostic_report: str) -> dict:
	"""DICOMweb viewer configuration for embedded PACS viewer page."""
	report = frappe.get_doc("Healthcare Diagnostic Report", diagnostic_report)
	wado = report.pacs_wado_url or _pacs_url(frappe._dict(patient=report.patient, name=report.based_on_service_request))
	return {
		"report": report.name,
		"patient": report.patient,
		"wado_url": wado,
		"viewer_mode": "dicomweb",
		"ohif_compatible": True,
	}


@frappe.whitelist()
def api_get_modality_worklist(branch: str, modality: str | None = None) -> list[dict]:
	"""DICOM Modality Worklist (MWL) — scheduled imaging procedures."""
	rows = api_get_radiology_worklist(branch, modality)
	for row in rows:
		row["mwl_status"] = "SCHEDULED"
		row["scheduled_procedure_step_id"] = row.get("name")
		row["patient_id"] = row.get("patient")
	return rows


@frappe.whitelist()
def api_mpps_update(service_request: str, status: str, performed_datetime: str | None = None) -> dict:
	"""DICOM MPPS — modality performed procedure step status."""
	sr = frappe.get_doc("Healthcare Service Request", service_request)
	allowed = {"IN PROGRESS", "COMPLETED", "DISCONTINUED"}
	if status not in allowed:
		frappe.throw(_("Invalid MPPS status"))
	if status == "COMPLETED":
		sr.db_set("status", "completed", update_modified=True)
	elif status == "DISCONTINUED":
		sr.db_set("status", "cancelled", update_modified=True)
	return {
		"service_request": sr.name,
		"mpps_status": status,
		"performed_datetime": performed_datetime or str(now_datetime()),
	}
