# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Whitelisted FHIR JSON export for interoperability (read-only)."""

import frappe
from frappe import _

from omnexa_healthcare.fhir.resource_builder import (
	build_fhir_allergy_intolerance,
	build_fhir_clinical_condition,
	build_fhir_diagnostic_report,
	build_fhir_encounter,
	build_fhir_episode_of_care,
	build_fhir_immunization,
	build_fhir_medication_statement,
	build_fhir_observation,
	build_fhir_patient,
	build_fhir_service_request,
)
from omnexa_healthcare.fhir.resource_bundle import build_patient_summary_ips_document_bundle


def _require_read(doctype: str, name: str):
	if not frappe.has_permission(doctype, "read", doc=name, throw=False):
		frappe.throw(_("Not permitted to read {0}").format(_(doctype)), frappe.PermissionError)


@frappe.whitelist()
def get_fhir_patient(patient: str) -> dict:
	"""Return a FHIR R4–style Patient resource dict for the given Healthcare Patient name."""
	patient = (patient or "").strip()
	if not patient:
		frappe.throw(_("patient is required"))
	_require_read("Healthcare Patient", patient)
	doc = frappe.get_doc("Healthcare Patient", patient)
	return build_fhir_patient(doc)


@frappe.whitelist()
def get_fhir_encounter(encounter: str) -> dict:
	"""Return a FHIR R4–style Encounter resource dict."""
	encounter = (encounter or "").strip()
	if not encounter:
		frappe.throw(_("encounter is required"))
	_require_read("Healthcare Encounter", encounter)
	doc = frappe.get_doc("Healthcare Encounter", encounter)
	return build_fhir_encounter(doc)


@frappe.whitelist()
def get_fhir_episode_of_care(episode: str) -> dict:
	"""Return a FHIR R4–style EpisodeOfCare resource dict."""
	episode = (episode or "").strip()
	if not episode:
		frappe.throw(_("episode is required"))
	_require_read("Healthcare Episode Of Care", episode)
	doc = frappe.get_doc("Healthcare Episode Of Care", episode)
	return build_fhir_episode_of_care(doc)


@frappe.whitelist()
def get_fhir_clinical_condition(condition: str) -> dict:
	"""Return a FHIR R4–style Condition resource dict."""
	condition = (condition or "").strip()
	if not condition:
		frappe.throw(_("condition is required"))
	_require_read("Healthcare Clinical Condition", condition)
	doc = frappe.get_doc("Healthcare Clinical Condition", condition)
	return build_fhir_clinical_condition(doc)


@frappe.whitelist()
def get_fhir_allergy_intolerance(allergy_intolerance: str) -> dict:
	"""Return a FHIR R4–style AllergyIntolerance resource dict."""
	allergy_intolerance = (allergy_intolerance or "").strip()
	if not allergy_intolerance:
		frappe.throw(_("allergy_intolerance is required"))
	_require_read("Healthcare Allergy Intolerance", allergy_intolerance)
	doc = frappe.get_doc("Healthcare Allergy Intolerance", allergy_intolerance)
	return build_fhir_allergy_intolerance(doc)


@frappe.whitelist()
def get_fhir_medication_statement(medication_statement: str) -> dict:
	"""Return a FHIR R4–style MedicationStatement resource dict."""
	medication_statement = (medication_statement or "").strip()
	if not medication_statement:
		frappe.throw(_("medication_statement is required"))
	_require_read("Healthcare Medication Statement", medication_statement)
	doc = frappe.get_doc("Healthcare Medication Statement", medication_statement)
	return build_fhir_medication_statement(doc)


@frappe.whitelist()
def get_fhir_medication_request(medication_request: str) -> dict:
	"""Return FHIR R4 MedicationRequest from Healthcare Medication Request."""
	medication_request = (medication_request or "").strip()
	if not medication_request:
		frappe.throw(_("medication_request is required"))
	if not frappe.db.exists("Healthcare Medication Request", medication_request):
		frappe.throw(_("Medication Request not found."))
	doc = frappe.get_doc("Healthcare Medication Request", medication_request)
	meds = [
		{
			"resourceType": "Medication",
			"code": {"text": row.drug_name, "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": row.rxnorm_code}] if row.rxnorm_code else []},
		}
		for row in doc.items or []
	]
	return {
		"resourceType": "MedicationRequest",
		"id": doc.name,
		"status": "active" if doc.status == "Signed" else "draft",
		"intent": "order",
		"subject": {"reference": f"Patient/{doc.patient}"},
		"requester": {"reference": f"Practitioner/{doc.practitioner}"},
		"authoredOn": str(doc.signed_on or doc.creation),
		"reasonCode": [{"text": doc.diagnosis}],
		"medicationCodeableConcept": meds[0]["code"] if meds else {"text": doc.diagnosis},
		"dosageInstruction": [{"text": row.instructions or f"{row.dose} {row.frequency}"} for row in doc.items or []],
	}


@frappe.whitelist()
def get_fhir_immunization(immunization: str) -> dict:
	"""Return a FHIR R4–style Immunization resource dict."""
	immunization = (immunization or "").strip()
	if not immunization:
		frappe.throw(_("immunization is required"))
	_require_read("Healthcare Immunization", immunization)
	doc = frappe.get_doc("Healthcare Immunization", immunization)
	return build_fhir_immunization(doc)


@frappe.whitelist()
def get_fhir_observation(observation: str) -> dict:
	"""Return a FHIR R4–style Observation resource dict (LOINC-mapped vitals)."""
	observation = (observation or "").strip()
	if not observation:
		frappe.throw(_("observation is required"))
	_require_read("Healthcare Observation", observation)
	doc = frappe.get_doc("Healthcare Observation", observation)
	return build_fhir_observation(doc)


@frappe.whitelist()
def get_fhir_service_request(service_request: str) -> dict:
	"""Return a FHIR R4–style ServiceRequest resource dict."""
	service_request = (service_request or "").strip()
	if not service_request:
		frappe.throw(_("service_request is required"))
	_require_read("Healthcare Service Request", service_request)
	doc = frappe.get_doc("Healthcare Service Request", service_request)
	return build_fhir_service_request(doc)


@frappe.whitelist()
def get_fhir_diagnostic_report(diagnostic_report: str) -> dict:
	"""Return a FHIR R4–style DiagnosticReport resource dict."""
	diagnostic_report = (diagnostic_report or "").strip()
	if not diagnostic_report:
		frappe.throw(_("diagnostic_report is required"))
	_require_read("Healthcare Diagnostic Report", diagnostic_report)
	doc = frappe.get_doc("Healthcare Diagnostic Report", diagnostic_report)
	return build_fhir_diagnostic_report(doc)


@frappe.whitelist()
def get_fhir_patient_summary_ips_bundle(patient: str) -> dict:
	"""Return a FHIR R4 **document** Bundle (HL7 IPS–inspired): Composition + Patient + clinical content."""
	patient = (patient or "").strip()
	if not patient:
		frappe.throw(_("patient is required"))
	return build_patient_summary_ips_document_bundle(patient)
