# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""LIS — lab workbench, barcode labels, HL7 ORU inbound, reference ranges."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today


@frappe.whitelist()
def api_get_lab_worklist(branch: str, status: str | None = None) -> list[dict]:
	if not branch:
		frappe.throw(_("Branch is required"))
	filters = {"branch": branch}
	if status:
		filters["status"] = status
	else:
		filters["status"] = ["in", ["planned", "collected", "in_lab"]]
	return frappe.get_all(
		"Healthcare Lab Sample",
		filters=filters,
		fields=["name", "patient", "patient_display", "specimen_id", "status", "collected_datetime", "sample_type"],
		order_by="collected_datetime asc",
		limit=200,
	)


@frappe.whitelist()
def api_generate_specimen_barcode(lab_sample: str) -> dict:
	doc = frappe.get_doc("Healthcare Lab Sample", lab_sample)
	if not doc.specimen_id:
		doc.specimen_id = f"SPC-{doc.name.split('-')[-1]}-{frappe.generate_hash(length=6).upper()}"
		doc.save()
	return {"specimen_id": doc.specimen_id, "barcode_text": doc.specimen_id}


@frappe.whitelist()
def api_apply_reference_range(test_name: str, value: float, gender: str | None = None, age: int | None = None) -> dict:
	filters = {"test_name": test_name}
	if gender:
		filters["gender"] = ["in", [gender, ""]]
	rows = frappe.get_all(
		"Healthcare Lab Reference Range",
		filters=filters,
		fields=["low_value", "high_value"],
		limit=1,
	)
	if not rows:
		return {"abnormal": False, "flag": "unknown"}
	row = rows[0]
	abnormal = flt(value) < flt(row.low_value) or flt(value) > flt(row.high_value)
	flag = "high" if flt(value) > flt(row.high_value) else "low" if flt(value) < flt(row.low_value) else "normal"
	return {"abnormal": abnormal, "flag": flag, "low": row.low_value, "high": row.high_value}


@frappe.whitelist()
def api_hl7_oru_inbound(message: str) -> dict:
	"""Parse minimal HL7 ORU^R01 and create/update DiagnosticReport."""
	if not message or "OBX|" not in message:
		frappe.throw(_("Invalid ORU message"))
	patient_id = _hl7_field(message, "PID", 3) or _hl7_field(message, "PID", 2)
	obx_value = _hl7_field(message, "OBX", 5)
	test_name = _hl7_field(message, "OBX", 3) or "Lab Result"
	patient = frappe.db.get_value("Healthcare Patient Identifier", {"value": patient_id}, "parent")
	if not patient:
		frappe.throw(_("Patient not found for ID {0}").format(patient_id))
	company, branch = frappe.db.get_value("Healthcare Patient", patient, ["company", "branch"])
	report = frappe.get_doc(
		{
			"doctype": "Healthcare Diagnostic Report",
			"naming_series": "DGR-.#####",
			"patient": patient,
			"company": company,
			"branch": branch,
			"report_category": "laboratory",
			"report_title": test_name,
			"status": "final",
			"effective_datetime": now_datetime(),
			"conclusion": obx_value,
			"abnormal_flag": 0,
		}
	).insert(ignore_permissions=True)
	return {"diagnostic_report": report.name}


@frappe.whitelist()
def api_astm_inbound(instrument_id: str, payload: str, protocol: str = "ASTM") -> dict:
	"""Store instrument message and link to lab sample when specimen id present."""
	import json

	data = payload
	specimen = None
	if payload.strip().startswith("{"):
		parsed = json.loads(payload)
		specimen = parsed.get("specimen_id")
		data = json.dumps(parsed)
	elif "|" in payload:
		for part in payload.split("|"):
			if part.startswith("SPC-") or part.startswith("S"):
				specimen = part
				break
	sample = None
	if specimen:
		sample = frappe.db.get_value("Healthcare Lab Sample", {"specimen_id": specimen}, "name")
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Lis Instrument Message",
			"instrument_id": instrument_id,
			"protocol": protocol,
			"direction": "Inbound",
			"payload": data,
			"lab_sample": sample,
			"status": "Received",
			"company": company,
		}
	).insert(ignore_permissions=True)
	return {"message": doc.name, "lab_sample": sample, "status": doc.status}


def _hl7_field(message: str, segment: str, field_idx: int) -> str | None:
	for line in message.split("\n"):
		line = line.strip("\r")
		if not line.startswith(segment + "|"):
			continue
		parts = line.split("|")
		if len(parts) > field_idx:
			return parts[field_idx].split("^")[0] or parts[field_idx]
	return None
