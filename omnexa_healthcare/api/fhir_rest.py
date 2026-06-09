# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""FHIR REST read/write subset — /api/method routing."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_healthcare.api.fhir_export import (
	get_fhir_allergy_intolerance,
	get_fhir_clinical_condition,
	get_fhir_encounter,
	get_fhir_patient,
)


READ_MAP = {
	"Patient": ("Healthcare Patient", get_fhir_patient, "patient"),
	"Encounter": ("Healthcare Encounter", get_fhir_encounter, "encounter"),
	"Condition": ("Healthcare Clinical Condition", get_fhir_clinical_condition, "condition"),
	"AllergyIntolerance": ("Healthcare Allergy Intolerance", get_fhir_allergy_intolerance, "allergy_intolerance"),
}

WRITE_MAP = {
	"Patient": "Healthcare Patient",
	"Encounter": "Healthcare Encounter",
}


@frappe.whitelist()
def fhir_read(resource_type: str, resource_id: str) -> dict:
	spec = READ_MAP.get(resource_type)
	if not spec:
		frappe.throw(_("Unsupported FHIR resource type: {0}").format(resource_type))
	_, fn, arg = spec
	return fn(resource_id)


@frappe.whitelist()
def fhir_search(resource_type: str, **kwargs) -> dict:
	doctype = READ_MAP.get(resource_type, (None,))[0]
	if not doctype:
		frappe.throw(_("Unsupported resource type"))
	limit = int(kwargs.pop("_count", 20) or 20)
	names = frappe.get_all(doctype, filters=kwargs, pluck="name", limit=limit)
	return {
		"resourceType": "Bundle",
		"type": "searchset",
		"total": len(names),
		"entry": [{"resource": fhir_read(resource_type, n)} for n in names],
	}


@frappe.whitelist()
def fhir_create(resource_type: str, payload: str | dict) -> dict:
	doctype = WRITE_MAP.get(resource_type)
	if not doctype:
		frappe.throw(_("Write not supported for {0}").format(resource_type))
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	if resource_type == "Patient":
		doc = frappe.get_doc({"doctype": doctype, **data}).insert()
	elif resource_type == "Encounter":
		doc = frappe.get_doc({"doctype": doctype, **data}).insert()
	else:
		frappe.throw(_("Unsupported write"))
	return fhir_read(resource_type, doc.name)
