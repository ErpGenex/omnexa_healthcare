# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Build FHIR R4–style resource dicts from Omnexa Healthcare documents (subset / best-effort)."""

from __future__ import annotations

from typing import Any

from frappe.model.document import Document
from frappe.utils import format_date, get_datetime


def _iso_date(d) -> str | None:
	if not d:
		return None
	return format_date(d)


def _iso_datetime(dt) -> str | None:
	if not dt:
		return None
	try:
		return get_datetime(dt).isoformat()
	except Exception:
		return str(dt)


def _strip_empty(obj: Any) -> Any:
	if isinstance(obj, dict):
		out = {}
		for k, v in obj.items():
			cv = _strip_empty(v)
			if cv is None:
				continue
			if cv == {} or cv == []:
				continue
			out[k] = cv
		return out or None
	if isinstance(obj, list):
		out = [_strip_empty(x) for x in obj]
		out = [x for x in out if x is not None and x != {} and x != []]
		return out or None
	return obj


def build_fhir_patient(doc: Document) -> dict[str, Any]:
	"""FHIR Patient (subset). Logical id = ERPGenEx document name."""
	name: dict[str, Any] = {"use": "official"}
	if doc.get("family_name"):
		name["family"] = doc.family_name
	givens = [g for g in [doc.get("given_name"), doc.get("middle_name")] if g]
	if givens:
		name["given"] = givens
	if doc.get("name_prefix"):
		name["prefix"] = [doc.name_prefix]
	if doc.get("name_suffix"):
		name["suffix"] = [doc.name_suffix]

	identifiers = []
	for row in doc.get("identifiers") or []:
		id_obj: dict[str, Any] = {
			"use": row.get("identifier_use") or "official",
			"value": row.value,
		}
		if row.get("system_uri"):
			id_obj["system"] = row.system_uri
		type_obj: dict[str, Any] = {"text": row.get("type_display") or row.get("identifier_type")}
		id_obj["type"] = type_obj
		identifiers.append(id_obj)

	telecom = []
	for row in doc.get("telecom") or []:
		telecom.append(
			{
				"system": row.get("contact_system"),
				"use": row.get("contact_use"),
				"value": row.value,
				"rank": row.get("rank"),
			}
		)

	address: dict[str, Any] = {}
	if doc.get("address_use"):
		address["use"] = doc.address_use
	if doc.get("address_type"):
		address["type"] = doc.address_type
	lines = [ln for ln in [doc.get("address_line1"), doc.get("address_line2")] if ln]
	if lines:
		address["line"] = lines
	for fhir_k, omx_k in (
		("district", "district"),
		("city", "city"),
		("state", "state"),
		("postalCode", "postal_code"),
	):
		if doc.get(omx_k):
			address[fhir_k] = doc.get(omx_k)
	if doc.get("country"):
		address["country"] = doc.country

	resource: dict[str, Any] = {
		"resourceType": "Patient",
		"id": doc.name,
		"meta": {
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-healthcare-patient",
					"display": "Omnexa Healthcare Patient",
				}
			]
		},
		"active": bool(doc.get("active")),
		"name": [name],
	}
	if doc.get("gender"):
		resource["gender"] = doc.gender
	if doc.get("birth_date"):
		resource["birthDate"] = _iso_date(doc.birth_date)
	if doc.get("deceased"):
		resource["deceasedBoolean"] = True
		if doc.get("deceased_datetime"):
			resource["deceasedDateTime"] = _iso_datetime(doc.deceased_datetime)
	if identifiers:
		resource["identifier"] = identifiers
	if telecom:
		resource["telecom"] = telecom
	if address:
		resource["address"] = [address]
	if doc.get("marital_status"):
		resource["maritalStatus"] = {"text": doc.marital_status}
	if doc.get("preferred_language"):
		resource["communication"] = [
			{
				"language": {"coding": [{"code": doc.preferred_language}]},
				"preferred": True,
			}
		]

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_encounter(doc: Document) -> dict[str, Any]:
	"""FHIR Encounter (subset)."""
	resource: dict[str, Any] = {
		"resourceType": "Encounter",
		"id": doc.name,
		"meta": {
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-healthcare-encounter",
					"display": "Omnexa Healthcare Encounter",
				}
			]
		},
		"status": doc.get("status"),
		"class": {
			"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
			"display": doc.get("encounter_class"),
		},
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"period": {"start": _iso_datetime(doc.get("period_start"))},
	}
	if doc.get("period_end"):
		resource["period"]["end"] = _iso_datetime(doc.period_end)
	if doc.get("encounter_type"):
		resource["type"] = [{"text": doc.encounter_type}]
	if doc.get("encounter_priority"):
		resource["priority"] = {
			"coding": [
				{
					"system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
					"code": doc.encounter_priority,
				}
			]
		}
	if doc.get("appointment"):
		resource["appointment"] = [
			{
				"reference": f"urn:erpgenex:healthcare-appointment:{doc.appointment}",
				"display": "Omnexa Healthcare Appointment",
			}
		]
	if doc.get("episode_of_care"):
		resource["episodeOfCare"] = [{"reference": f"EpisodeOfCare/{doc.episode_of_care}"}]
	if doc.get("chief_complaint"):
		resource["reasonCode"] = [{"text": doc.chief_complaint}]
	elif doc.get("reason_for_visit"):
		resource["reasonCode"] = [{"text": doc.reason_for_visit}]

	diagnosis = []
	for row in doc.get("diagnoses") or []:
		dx = {"condition": {"display": row.description}}
		if row.get("icd10_code"):
			dx["condition"]["coding"] = [{"system": "http://hl7.org/fhir/sid/icd-10", "code": row.icd10_code}]
		diagnosis.append(dx)
	if diagnosis:
		resource["diagnosis"] = diagnosis

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_episode_of_care(doc: Document) -> dict[str, Any]:
	"""FHIR EpisodeOfCare (subset)."""
	resource: dict[str, Any] = {
		"resourceType": "EpisodeOfCare",
		"id": doc.name,
		"meta": {
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-healthcare-episode",
					"display": "Omnexa Healthcare Episode Of Care",
				}
			]
		},
		"status": doc.get("status"),
		"type": [{"text": doc.get("episode_type")}],
		"patient": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"period": {"start": _iso_date(doc.get("period_start"))},
		"title": doc.get("episode_title"),
	}
	if doc.get("period_end"):
		resource["period"]["end"] = _iso_date(doc.period_end)
	if doc.get("description"):
		resource["description"] = doc.description

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_clinical_condition(doc: Document) -> dict[str, Any]:
	"""FHIR Condition (problem / diagnosis record)."""
	resource: dict[str, Any] = {
		"resourceType": "Condition",
		"id": doc.name,
		"meta": {
			"profile": ["http://hl7.org/fhir/StructureDefinition/Condition"],
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-healthcare-condition",
					"display": "Omnexa Healthcare Clinical Condition",
				}
			],
		},
		"clinicalStatus": {
			"coding": [
				{
					"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
					"code": doc.get("clinical_status"),
				}
			]
		},
		"verificationStatus": {
			"coding": [
				{
					"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
					"code": doc.get("verification_status"),
				}
			]
		},
		"category": [
			{
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/condition-category",
						"code": doc.get("category"),
					}
				]
			}
		],
		"code": {"text": doc.get("clinical_description")},
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
	}
	if doc.get("icd10_code"):
		resource["code"]["coding"] = [
			{
				"system": "http://hl7.org/fhir/sid/icd-10",
				"code": doc.icd10_code,
				"display": doc.get("clinical_description"),
			}
		]
	if doc.get("severity"):
		resource["severity"] = {"text": doc.severity}
	if doc.get("onset_datetime"):
		resource["onsetDateTime"] = _iso_datetime(doc.onset_datetime)
	if doc.get("abatement_datetime"):
		resource["abatementDateTime"] = _iso_datetime(doc.abatement_datetime)
	if doc.get("recorded_date"):
		resource["recordedDate"] = _iso_date(doc.recorded_date)
	if doc.get("encounter"):
		resource["encounter"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("episode_of_care"):
		resource.setdefault("extension", []).append(
			{
				"url": "https://omnexa.com/fhir/StructureDefinition/context-episode-of-care",
				"valueReference": {"reference": f"EpisodeOfCare/{doc.episode_of_care}"},
			}
		)

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_allergy_intolerance(doc: Document) -> dict[str, Any]:
	"""FHIR AllergyIntolerance."""
	reaction = None
	if doc.get("reaction_manifestation"):
		reaction = [
			{
				"manifestation": [
					{
						"text": doc.reaction_manifestation,
					}
				]
			}
		]

	resource: dict[str, Any] = {
		"resourceType": "AllergyIntolerance",
		"id": doc.name,
		"meta": {
			"profile": ["http://hl7.org/fhir/StructureDefinition/AllergyIntolerance"],
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-healthcare-allergy",
					"display": "Omnexa Healthcare Allergy Intolerance",
				}
			],
		},
		"clinicalStatus": {
			"coding": [
				{
					"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
					"code": doc.get("clinical_status"),
				}
			]
		},
		"verificationStatus": {
			"coding": [
				{
					"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
					"code": doc.get("verification_status"),
				}
			]
		},
		"type": doc.get("allergy_type"),
		"category": [
			{
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-category",
						"code": doc.get("category"),
					}
				]
			}
		],
		"criticality": doc.get("criticality"),
		"patient": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"code": {"text": doc.get("substance_text")},
	}
	if doc.get("onset_datetime"):
		resource["onsetDateTime"] = _iso_datetime(doc.onset_datetime)
	if reaction:
		resource["reaction"] = reaction
	if doc.get("notes"):
		resource["note"] = [{"text": doc.notes}]

	stripped = _strip_empty(resource)
	return stripped or resource


OBSERVATION_PROFILE_META: dict[str, dict[str, str | None]] = {
	"heart_rate": {"loinc": "8867-4", "display": "Heart rate", "ucum": "/min"},
	"spo2": {"loinc": "2708-6", "display": "Oxygen saturation in Arterial blood", "ucum": "%"},
	"body_temperature": {"loinc": "8310-5", "display": "Body temperature", "ucum": "Cel"},
	"body_weight": {"loinc": "29463-7", "display": "Body weight", "ucum": "kg"},
	"body_height": {"loinc": "8302-2", "display": "Body height", "ucum": "cm"},
	"blood_pressure": {"loinc": "85354-9", "display": "Blood pressure panel with all children optional", "ucum": None},
	"lab_glucose": {"loinc": "2345-7", "display": "Glucose [Mass/volume] in Serum or Plasma", "ucum": "mg/dL"},
	"lab_hemoglobin": {"loinc": "718-7", "display": "Hemoglobin [Mass/volume] in Blood", "ucum": "g/dL"},
}

VITAL_SIGN_PROFILES = frozenset(
	{"heart_rate", "spo2", "body_temperature", "body_weight", "body_height", "blood_pressure"}
)


def _ips_document_bundle_ref(resource_type: str, logical_id: str) -> str:
	"""Reference string matching IPS document Bundle entry fullUrl convention."""
	return f"urn:erpgenex:ips:r4:{resource_type}:{logical_id}"


def build_fhir_medication_statement(doc: Document) -> dict[str, Any]:
	"""FHIR MedicationStatement (medication as CodeableConcept text; map to RxNorm externally)."""
	resource: dict[str, Any] = {
		"resourceType": "MedicationStatement",
		"id": doc.name,
		"meta": {
			"profile": ["http://hl7.org/fhir/StructureDefinition/MedicationStatement"],
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-medication-statement",
					"display": "Omnexa Healthcare Medication Statement",
				}
			],
		},
		"status": doc.get("status"),
		"category": [
			{
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
						"code": doc.get("category"),
					}
				]
			}
		],
		"medicationCodeableConcept": {"text": doc.get("medication_text")},
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
	}
	if doc.get("dosage_text"):
		resource["dosage"] = [{"text": doc.dosage_text}]
	if doc.get("effective_period_start") or doc.get("effective_period_end"):
		resource["effectivePeriod"] = {}
		if doc.get("effective_period_start"):
			resource["effectivePeriod"]["start"] = _iso_date(doc.effective_period_start)
		if doc.get("effective_period_end"):
			resource["effectivePeriod"]["end"] = _iso_date(doc.effective_period_end)
	if doc.get("encounter"):
		resource["context"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("notes"):
		resource["note"] = [{"text": doc.notes}]

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_immunization(doc: Document) -> dict[str, Any]:
	"""FHIR Immunization."""
	vaccine_code: dict[str, Any] = {"text": doc.get("vaccine_name")}
	if doc.get("cvx_code"):
		vaccine_code["coding"] = [
			{"system": "http://hl7.org/fhir/sid/cvx", "code": doc.cvx_code, "display": doc.get("vaccine_name")}
		]

	resource: dict[str, Any] = {
		"resourceType": "Immunization",
		"id": doc.name,
		"meta": {
			"profile": ["http://hl7.org/fhir/StructureDefinition/Immunization"],
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-immunization",
					"display": "Omnexa Healthcare Immunization",
				}
			],
		},
		"status": doc.get("status"),
		"vaccineCode": vaccine_code,
		"patient": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"occurrenceDateTime": _iso_datetime(doc.get("occurrence_datetime")),
	}
	if doc.get("lot_number"):
		resource["lotNumber"] = doc.lot_number
	if doc.get("site"):
		resource["site"] = {"text": doc.site}
	if doc.get("encounter"):
		resource["encounter"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("notes"):
		resource["note"] = [{"text": doc.notes}]

	stripped = _strip_empty(resource)
	return stripped or resource


def build_fhir_observation(doc: Document) -> dict[str, Any]:
	"""FHIR Observation (LOINC-mapped vitals or lab-style results; BP as multi-component panel)."""
	meta = OBSERVATION_PROFILE_META.get(doc.observation_profile) or {}
	loinc = meta.get("loinc")
	display = meta.get("display")
	if doc.observation_profile in VITAL_SIGN_PROFILES:
		obs_profiles = ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
	else:
		obs_profiles = ["http://hl7.org/fhir/StructureDefinition/Observation"]

	resource: dict[str, Any] = {
		"resourceType": "Observation",
		"id": doc.name,
		"meta": {
			"profile": obs_profiles,
			"tag": [
				{
					"system": "https://omnexa.com/fhir/structure",
					"code": "erpgenex-observation",
					"display": "Omnexa Healthcare Observation",
				}
			],
		},
		"status": doc.get("status"),
		"category": [
			{
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/observation-category",
						"code": doc.get("category") or "vital-signs",
					}
				]
			}
		],
		"code": {
			"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}],
			"text": display,
		},
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"effectiveDateTime": _iso_datetime(doc.get("effective_datetime")),
	}

	if doc.observation_profile == "blood_pressure":
		resource["component"] = [
			{
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "8480-6",
							"display": "Systolic blood pressure",
						}
					]
				},
				"valueQuantity": {
					"value": doc.value_primary,
					"unit": "mmHg",
					"system": "http://unitsofmeasure.org",
					"code": "mm[Hg]",
				},
			},
			{
				"code": {
					"coding": [
						{
							"system": "http://loinc.org",
							"code": "8462-4",
							"display": "Diastolic blood pressure",
						}
					]
				},
				"valueQuantity": {
					"value": doc.value_secondary,
					"unit": "mmHg",
					"system": "http://unitsofmeasure.org",
					"code": "mm[Hg]",
				},
			},
		]
	else:
		ucum = (doc.get("unit_ucum") or meta.get("ucum") or "").strip()
		resource["valueQuantity"] = {
			"value": doc.value_primary,
			"system": "http://unitsofmeasure.org",
		}
		if ucum:
			resource["valueQuantity"]["code"] = ucum
			resource["valueQuantity"]["unit"] = ucum

	if doc.get("encounter"):
		resource["encounter"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("notes"):
		resource["note"] = [{"text": doc.notes}]

	stripped = _strip_empty(resource)
	return stripped or resource


SERVICE_REQUEST_CATEGORY_CODE: dict[str, str] = {
	"laboratory": "108252007",
	"imaging": "363679005",
	"counseling": "409063005",
	"social": "410223002",
	"other": "386053000",
}

SERVICE_REQUEST_CATEGORY_DISPLAY: dict[str, str] = {
	"laboratory": "Laboratory procedure",
	"imaging": "Imaging",
	"counseling": "Counseling",
	"social": "Social service",
	"other": "Evaluation procedure",
}


def build_fhir_service_request(doc: Document) -> dict[str, Any]:
	"""FHIR ServiceRequest (orders; SNOMED procedure hierarchy for category when possible)."""
	cat = doc.get("request_category") or "laboratory"
	code = SERVICE_REQUEST_CATEGORY_CODE.get(cat, SERVICE_REQUEST_CATEGORY_CODE["other"])
	disp = SERVICE_REQUEST_CATEGORY_DISPLAY.get(cat, SERVICE_REQUEST_CATEGORY_DISPLAY["other"])

	code_obj: dict[str, Any] = {"text": doc.get("request_title")}
	if doc.get("request_loinc"):
		code_obj["coding"] = [
			{
				"system": "http://loinc.org",
				"code": doc.request_loinc,
				"display": doc.get("request_title"),
			}
		]

	resource: dict[str, Any] = {
		"resourceType": "ServiceRequest",
		"id": doc.name,
		"meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/ServiceRequest"]},
		"status": doc.get("status"),
		"intent": doc.get("intent"),
		"priority": doc.get("priority"),
		"category": [
			{
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": code,
						"display": disp,
					}
				],
				"text": disp,
			}
		],
		"code": code_obj,
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"authoredOn": _iso_datetime(doc.get("authored_on")),
	}
	if doc.get("encounter"):
		resource["encounter"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("note"):
		resource["note"] = [{"text": doc.note}]

	stripped = _strip_empty(resource)
	return stripped or resource


DIAGNOSTIC_REPORT_V2_0074: dict[str, tuple[str, str]] = {
	"laboratory": ("LAB", "Laboratory"),
	"radiology": ("RAD", "Radiology"),
	"pathology": ("PAT", "Pathology"),
	"other": ("OTH", "Other"),
}


def build_fhir_diagnostic_report(doc: Document) -> dict[str, Any]:
	"""FHIR DiagnosticReport; result references use bundle fullUrl style for document Bundles."""
	v2 = DIAGNOSTIC_REPORT_V2_0074.get(doc.get("report_category") or "laboratory", ("OTH", "Other"))
	code_obj: dict[str, Any] = {"text": doc.get("report_title")}
	if doc.get("report_loinc"):
		code_obj["coding"] = [
			{
				"system": "http://loinc.org",
				"code": doc.report_loinc,
				"display": doc.get("report_title"),
			}
		]

	resource: dict[str, Any] = {
		"resourceType": "DiagnosticReport",
		"id": doc.name,
		"meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"]},
		"status": doc.get("status"),
		"category": [
			{
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/v2-0074",
						"code": v2[0],
						"display": v2[1],
					}
				]
			}
		],
		"code": code_obj,
		"subject": {"reference": f"Patient/{doc.patient}", "type": "Patient"},
		"effectiveDateTime": _iso_datetime(doc.get("effective_datetime")),
	}
	if doc.get("encounter"):
		resource["encounter"] = {"reference": f"Encounter/{doc.encounter}"}
	if doc.get("based_on_service_request"):
		resource["basedOn"] = [
			{"reference": _ips_document_bundle_ref("ServiceRequest", doc.based_on_service_request)}
		]

	result: list[dict[str, Any]] = []
	narrative_lines: list[str] = []
	for row in doc.get("findings") or []:
		if row.get("linked_observation"):
			result.append(
				{"reference": _ips_document_bundle_ref("Observation", row.linked_observation)}
			)
		if row.get("finding_narrative"):
			narrative_lines.append(row.finding_narrative)
	if result:
		resource["result"] = result

	conclusion_parts = [p for p in [doc.get("conclusion")] if p]
	conclusion_parts.extend(narrative_lines)
	if conclusion_parts:
		resource["conclusion"] = "\n".join(conclusion_parts)

	stripped = _strip_empty(resource)
	return stripped or resource
