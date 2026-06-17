# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""FHIR Bulk Data $export — patient compartment export."""

from __future__ import annotations

import json

import frappe
from frappe import _

from omnexa_healthcare.api.fhir_export import (
	get_fhir_allergy_intolerance,
	get_fhir_clinical_condition,
	get_fhir_encounter,
	get_fhir_immunization,
	get_fhir_medication_statement,
	get_fhir_observation,
	get_fhir_patient,
)


EXPORT_RESOURCE_FNS = {
	"Patient": get_fhir_patient,
	"Encounter": get_fhir_encounter,
	"Condition": get_fhir_clinical_condition,
	"AllergyIntolerance": get_fhir_allergy_intolerance,
	"MedicationStatement": get_fhir_medication_statement,
	"Immunization": get_fhir_immunization,
	"Observation": get_fhir_observation,
}


@frappe.whitelist()
def fhir_bulk_export(patient: str | None = None, company: str | None = None, resource_types: str | list | None = None) -> dict:
	"""Bulk export FHIR resources for a patient or company cohort."""
	if isinstance(resource_types, str):
		resource_types = json.loads(resource_types) if resource_types else list(EXPORT_RESOURCE_FNS.keys())
	resource_types = resource_types or list(EXPORT_RESOURCE_FNS.keys())
	entries = []
	if patient:
		for rt in resource_types:
			fn = EXPORT_RESOURCE_FNS.get(rt)
			if not fn:
				continue
			if rt == "Patient":
				entries.append({"resourceType": rt, "resource": fn(patient)})
				continue
			doctype_map = {
				"Encounter": "Healthcare Encounter",
				"Condition": "Healthcare Clinical Condition",
				"AllergyIntolerance": "Healthcare Allergy Intolerance",
				"MedicationStatement": "Healthcare Medication Statement",
				"Immunization": "Healthcare Immunization",
				"Observation": "Healthcare Observation",
			}
			dt = doctype_map.get(rt)
			if not dt:
				continue
			for name in frappe.get_all(dt, filters={"patient": patient}, pluck="name", limit=500):
				entries.append({"resourceType": rt, "resource": fn(name)})
	elif company:
		for p in frappe.get_all("Healthcare Patient", filters={"company": company}, pluck="name", limit=100):
			sub = fhir_bulk_export(patient=p, resource_types=resource_types)
			entries.extend(sub.get("entry") or [])
	else:
		frappe.throw(_("patient or company is required for bulk export."))
	return {
		"resourceType": "Bundle",
		"type": "collection",
		"timestamp": frappe.utils.now_datetime(),
		"total": len(entries),
		"entry": entries,
	}


@frappe.whitelist()
def get_read_replica_guide() -> dict:
	return {
		"title": "Omnexa Healthcare — Read Replica Deployment Guide",
		"version": "2026.06",
		"recommendations": [
			"Route analytics reports and FHIR $export to read replica connection.",
			"Use site_config.db_replica_host for reporting workers.",
			"Keep write path on primary MariaDB/PostgreSQL only.",
			"Monitor replication lag < 5s for clinical dashboards.",
		],
	}
