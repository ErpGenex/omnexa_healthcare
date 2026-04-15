# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""FHIR Bundle builders aligned with HL7 IPS (International Patient Summary) patterns."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

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


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _full_url(resource_type: str, logical_id: str) -> str:
	return f"urn:erpgenex:ips:r4:{resource_type}:{logical_id}"


def _can_read(doctype: str, name: str) -> bool:
	return bool(frappe.has_permission(doctype, "read", doc=name, throw=False))


def _build_ips_composition(
	patient_id: str,
	patient_full_url: str,
	allergy_urls: list[str],
	condition_urls: list[str],
	episode_urls: list[str],
	encounter_urls: list[str],
	medication_urls: list[str],
	immunization_urls: list[str],
	vital_sign_observation_urls: list[str],
	diagnostic_result_observation_urls: list[str],
	diagnostic_report_urls: list[str],
	service_request_urls: list[str],
) -> dict[str, Any]:
	sections: list[dict[str, Any]] = []
	if allergy_urls:
		sections.append(
			{
				"title": "Allergies and intolerances",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "48765-2",
							"display": "Allergies and adverse reactions Document",
						}
					]
				},
				"entry": [{"reference": u} for u in allergy_urls],
			}
		)
	if condition_urls:
		sections.append(
			{
				"title": "Problems",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "11450-4",
							"display": "Problem list - Reported",
						}
					]
				},
				"entry": [{"reference": u} for u in condition_urls],
			}
		)
	if medication_urls:
		sections.append(
			{
				"title": "Medications",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "10160-0",
							"display": "History of Medication use Narrative",
						}
					]
				},
				"entry": [{"reference": u} for u in medication_urls],
			}
		)
	if immunization_urls:
		sections.append(
			{
				"title": "Immunizations",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "11369-6",
							"display": "History of Immunization narrative",
						}
					]
				},
				"entry": [{"reference": u} for u in immunization_urls],
			}
		)
	if service_request_urls:
		sections.append(
			{
				"title": "Service requests",
				"entry": [{"reference": u} for u in service_request_urls],
			}
		)
	diagnostic_section_entries = [*diagnostic_result_observation_urls, *diagnostic_report_urls]
	if diagnostic_section_entries:
		sections.append(
			{
				"title": "Relevant diagnostic tests and/or laboratory data",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "30954-2",
							"display": "Relevant diagnostic tests and/or laboratory data",
						}
					]
				},
				"entry": [{"reference": u} for u in diagnostic_section_entries],
			}
		)
	if vital_sign_observation_urls:
		sections.append(
			{
				"title": "Vital signs",
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "8716-3",
							"display": "Vital signs",
						}
					]
				},
				"entry": [{"reference": u} for u in vital_sign_observation_urls],
			}
		)
	if episode_urls:
		sections.append(
			{
				"title": "Care episodes",
				"entry": [{"reference": u} for u in episode_urls],
			}
		)
	if encounter_urls:
		sections.append(
			{
				"title": "Encounters",
				"entry": [{"reference": u} for u in encounter_urls],
			}
		)

	return {
		"resourceType": "Composition",
		"id": f"ips-composition-{patient_id}",
		"meta": {"profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Composition-uv-ips"]},
		"status": "final",
		"type": {
			"coding": [
				{
					"system": "http://loinc.org",
					"code": "60591-5",
					"display": "Patient summary Document",
				}
			]
		},
		"author": [
			{
				"identifier": {
					"system": "https://omnexa.com/fhir/composition-author",
					"value": "omnexa-erpgenex-healthcare",
				},
				"display": "Omnexa Healthcare (ERPGenEx)",
			}
		],
		"subject": {"reference": patient_full_url},
		"date": _utc_now_iso(),
		"title": "International Patient Summary (Omnexa clinical subset)",
		"section": sections,
	}


def build_patient_summary_ips_document_bundle(patient_id: str) -> dict[str, Any]:
	"""FHIR R4 document Bundle (IPS): Composition + Patient + IPS-aligned clinical sections (LOINC-coded)."""
	if not _can_read("Healthcare Patient", patient_id):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	patient_doc = frappe.get_doc("Healthcare Patient", patient_id)
	patient_url = _full_url("Patient", patient_id)
	patient_resource = build_fhir_patient(patient_doc)

	include_lab_obs_in_ips_section = True
	try:
		raw = frappe.db.get_single_value("Healthcare Settings", "include_lab_observations_in_ips_bundle")
		if raw is not None:
			include_lab_obs_in_ips_section = bool(cint(raw))
	except Exception:
		include_lab_obs_in_ips_section = True

	entry: list[dict[str, Any]] = []
	allergy_urls: list[str] = []
	condition_urls: list[str] = []
	episode_urls: list[str] = []
	encounter_urls: list[str] = []
	medication_urls: list[str] = []
	immunization_urls: list[str] = []
	vital_sign_observation_urls: list[str] = []
	diagnostic_result_observation_urls: list[str] = []
	service_request_urls: list[str] = []
	diagnostic_report_urls: list[str] = []

	for name in frappe.get_all(
		"Healthcare Allergy Intolerance",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=50,
	):
		if not _can_read("Healthcare Allergy Intolerance", name):
			continue
		url = _full_url("AllergyIntolerance", name)
		allergy_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_allergy_intolerance(
					frappe.get_doc("Healthcare Allergy Intolerance", name)
				),
			}
		)

	for name in frappe.get_all(
		"Healthcare Clinical Condition",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=100,
	):
		if not _can_read("Healthcare Clinical Condition", name):
			continue
		url = _full_url("Condition", name)
		condition_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_clinical_condition(frappe.get_doc("Healthcare Clinical Condition", name)),
			}
		)

	for name in frappe.get_all(
		"Healthcare Medication Statement",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=80,
	):
		if not _can_read("Healthcare Medication Statement", name):
			continue
		url = _full_url("MedicationStatement", name)
		medication_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_medication_statement(
					frappe.get_doc("Healthcare Medication Statement", name)
				),
			}
		)

	for name in frappe.get_all(
		"Healthcare Immunization",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=80,
	):
		if not _can_read("Healthcare Immunization", name):
			continue
		url = _full_url("Immunization", name)
		immunization_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_immunization(frappe.get_doc("Healthcare Immunization", name)),
			}
		)

	for name in frappe.get_all(
		"Healthcare Observation",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=100,
	):
		if not _can_read("Healthcare Observation", name):
			continue
		od = frappe.get_doc("Healthcare Observation", name)
		url = _full_url("Observation", name)
		entry.append({"fullUrl": url, "resource": build_fhir_observation(od)})
		cat = od.get("category") or "vital-signs"
		if cat == "vital-signs":
			vital_sign_observation_urls.append(url)
		elif cat in ("laboratory", "exam"):
			if include_lab_obs_in_ips_section:
				diagnostic_result_observation_urls.append(url)
		else:
			vital_sign_observation_urls.append(url)

	for name in frappe.get_all(
		"Healthcare Episode Of Care",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=30,
	):
		if not _can_read("Healthcare Episode Of Care", name):
			continue
		url = _full_url("EpisodeOfCare", name)
		episode_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_episode_of_care(frappe.get_doc("Healthcare Episode Of Care", name)),
			}
		)

	for name in frappe.get_all(
		"Healthcare Encounter",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=40,
	):
		if not _can_read("Healthcare Encounter", name):
			continue
		url = _full_url("Encounter", name)
		encounter_urls.append(url)
		entry.append(
			{"fullUrl": url, "resource": build_fhir_encounter(frappe.get_doc("Healthcare Encounter", name))}
		)

	for name in frappe.get_all(
		"Healthcare Service Request",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=50,
	):
		if not _can_read("Healthcare Service Request", name):
			continue
		url = _full_url("ServiceRequest", name)
		service_request_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_service_request(frappe.get_doc("Healthcare Service Request", name)),
			}
		)

	for name in frappe.get_all(
		"Healthcare Diagnostic Report",
		filters={"patient": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=40,
	):
		if not _can_read("Healthcare Diagnostic Report", name):
			continue
		url = _full_url("DiagnosticReport", name)
		diagnostic_report_urls.append(url)
		entry.append(
			{
				"fullUrl": url,
				"resource": build_fhir_diagnostic_report(frappe.get_doc("Healthcare Diagnostic Report", name)),
			}
		)

	composition = _build_ips_composition(
		patient_id,
		patient_url,
		allergy_urls,
		condition_urls,
		episode_urls,
		encounter_urls,
		medication_urls,
		immunization_urls,
		vital_sign_observation_urls,
		diagnostic_result_observation_urls,
		diagnostic_report_urls,
		service_request_urls,
	)
	composition_url = _full_url("Composition", f"ips-{patient_id}")

	ordered: list[dict[str, Any]] = [
		{"fullUrl": composition_url, "resource": composition},
		{"fullUrl": patient_url, "resource": patient_resource},
		*entry,
	]

	return {
		"resourceType": "Bundle",
		"type": "document",
		"timestamp": _utc_now_iso(),
		"meta": {"profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Bundle-uv-ips"]},
		"identifier": {
			"system": "https://omnexa.com/fhir/ips-bundle-id",
			"value": f"ips-omnexa-{patient_id}",
		},
		"entry": ordered,
	}
