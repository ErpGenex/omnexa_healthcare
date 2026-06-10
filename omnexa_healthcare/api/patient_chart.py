# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Integrated patient medical file (FHIR IPS–aligned summary + clinical timeline)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_healthcare.api.fhir_export import get_fhir_patient, get_fhir_patient_summary_ips_bundle


@frappe.whitelist()
def get_patient_medical_file(patient: str) -> dict:
	if not patient:
		frappe.throw(_("patient is required"))
	if not frappe.has_permission("Healthcare Patient", "read", patient):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Healthcare Patient", patient)
	filters = {"patient": patient, "docstatus": ["<", 2]}

	def _rows(doctype: str, fields: list[str], order_by: str, limit: int = 40):
		if not frappe.db.exists("DocType", doctype):
			return []
		return frappe.get_all(doctype, filters=filters, fields=fields, order_by=order_by, limit=limit)

	return {
		"patient": {
			"name": doc.name,
			"full_name": doc.full_name,
			"gender": doc.gender,
			"birth_date": doc.birth_date,
			"branch": doc.branch,
			"company": doc.company,
			"managing_facility": doc.managing_facility,
			"identifiers": [row.as_dict() for row in doc.identifiers or []],
			"telecom": [row.as_dict() for row in doc.telecom or []],
		},
		"fhir_patient": get_fhir_patient(patient),
		"ips_bundle": get_fhir_patient_summary_ips_bundle(patient),
		"episodes": _rows(
			"Healthcare Episode Of Care",
			["name", "status", "period_start", "period_end", "care_manager"],
			"period_start desc",
			20,
		),
		"appointments": _rows(
			"Healthcare Appointment",
			["name", "appointment_date", "status", "practitioner", "specialty", "booking_channel"],
			"appointment_date desc",
		),
		"encounters": _rows(
			"Healthcare Encounter",
			["name", "period_start", "status", "encounter_type", "practitioner"],
			"period_start desc",
		),
		"conditions": _rows(
			"Healthcare Clinical Condition",
			["name", "icd10_code", "clinical_description", "clinical_status"],
			"modified desc",
			30,
		),
		"allergies": _rows(
			"Healthcare Allergy Intolerance",
			["name", "substance_text", "criticality", "clinical_status"],
			"modified desc",
			30,
		),
		"medications": _rows(
			"Healthcare Medication Statement",
			["name", "medication_text", "dosage_text", "status"],
			"modified desc",
			30,
		),
		"observations": _rows(
			"Healthcare Observation",
			["name", "observation_profile", "value_primary", "value_secondary", "unit_ucum", "effective_datetime"],
			"effective_datetime desc",
			30,
		),
		"service_requests": _rows(
			"Healthcare Service Request",
			["name", "request_title", "request_category", "status", "authored_on"],
			"authored_on desc",
			30,
		),
		"diagnostic_reports": _rows(
			"Healthcare Diagnostic Report",
			["name", "report_title", "report_category", "status", "effective_datetime", "abnormal_flag"],
			"effective_datetime desc",
			30,
		),
		"admissions": _rows(
			"Healthcare Admission",
			["name", "status", "admission_datetime", "bed"],
			"admission_datetime desc",
			20,
		),
		"er_visits": _rows(
			"Healthcare Er Visit",
			["name", "arrival_datetime", "esi_level", "status", "chief_complaint"],
			"arrival_datetime desc",
			20,
		),
	}
