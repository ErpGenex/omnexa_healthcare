#!/usr/bin/env python3
"""Scaffold Epic-parity DocTypes (ER, ADT, CDS, RCM EDI, mobile, AI)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "omnexa_healthcare" / "doctype"
PERMS = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
	{"role": "Company Admin", "read": 1, "write": 1, "create": 1, "delete": 0},
	{"role": "Physician", "read": 1, "write": 1, "create": 1, "delete": 0},
	{"role": "Nursing User", "read": 1, "write": 1, "create": 1, "delete": 0},
	{"role": "Desk User", "read": 1, "write": 1, "create": 1, "delete": 0},
]

SPECS = [
	("healthcare_er_visit", {
		"autoname": "format:ERV-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1, "in_list_view": 1},
			{"fieldname": "arrival_datetime", "fieldtype": "Datetime", "label": "Arrival", "reqd": 1, "in_list_view": 1},
			{"fieldname": "esi_level", "fieldtype": "Select", "label": "ESI Triage", "options": "1\n2\n3\n4\n5", "reqd": 1, "in_list_view": 1},
			{"fieldname": "chief_complaint", "fieldtype": "Small Text", "label": "Chief Complaint"},
			{"default": "Registered", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Registered\nTriaged\nIn Treatment\nDisposition\nCompleted\nLWBS", "in_list_view": 1},
			{"fieldname": "track", "fieldtype": "Select", "label": "Track", "options": "Main\nFast Track\nTrauma\nResuscitation"},
			{"fieldname": "encounter", "fieldtype": "Link", "label": "Encounter", "options": "Healthcare Encounter"},
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission"},
			{"fieldname": "disposition", "fieldtype": "Select", "label": "Disposition", "options": "\nDischarge\nAdmit\nTransfer\nAMA\nExpired"},
			{"fieldname": "practitioner", "fieldtype": "Link", "label": "Attending", "options": "Healthcare Practitioner"},
		],
	}),
	("healthcare_in_basket_item", {
		"autoname": "format:IBK-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "recipient", "fieldtype": "Link", "label": "Recipient", "options": "User", "reqd": 1, "in_list_view": 1},
			{"fieldname": "item_type", "fieldtype": "Select", "label": "Type", "options": "Result\nSignature\nRefill\nTask\nCritical", "reqd": 1, "in_list_view": 1},
			{"fieldname": "reference_doctype", "fieldtype": "Link", "label": "Reference DocType", "options": "DocType"},
			{"fieldname": "reference_name", "fieldtype": "Dynamic Link", "label": "Reference", "options": "reference_doctype"},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "in_list_view": 1},
			{"default": "Open", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nDone\nCancelled", "in_list_view": 1},
			{"default": "Routine", "fieldname": "priority", "fieldtype": "Select", "label": "Priority", "options": "Routine\nUrgent\nCritical"},
			{"fieldname": "subject", "fieldtype": "Data", "label": "Subject", "reqd": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_clinical_cds_rule", {
		"autoname": "format:CDS-{#####}",
		"fields": [
			{"fieldname": "rule_name", "fieldtype": "Data", "label": "Rule Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "trigger_event", "fieldtype": "Select", "label": "Trigger", "options": "Medication Order\nLab Order\nDiagnosis\nAllergy", "reqd": 1},
			{"fieldname": "match_field", "fieldtype": "Data", "label": "Match Value"},
			{"fieldname": "severity", "fieldtype": "Select", "label": "Severity", "options": "Info\nWarning\nCritical\nContraindicated", "reqd": 1},
			{"fieldname": "message", "fieldtype": "Small Text", "label": "Message", "reqd": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_snomed_code", {
		"autoname": "field:concept_id",
		"fields": [
			{"fieldname": "concept_id", "fieldtype": "Data", "label": "SNOMED Concept ID", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "term", "fieldtype": "Data", "label": "Preferred Term", "reqd": 1, "in_list_view": 1},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_adt_transfer", {
		"autoname": "format:ADT-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission", "reqd": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "from_bed", "fieldtype": "Link", "label": "From Bed", "options": "Healthcare Bed"},
			{"fieldname": "to_bed", "fieldtype": "Link", "label": "To Bed", "options": "Healthcare Bed", "reqd": 1},
			{"fieldname": "transfer_datetime", "fieldtype": "Datetime", "label": "Transfer Time", "reqd": 1},
			{"fieldname": "reason", "fieldtype": "Small Text", "label": "Reason"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_nursing_care_plan", {
		"autoname": "format:NCP-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission", "reqd": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "nursing_diagnosis", "fieldtype": "Small Text", "label": "Nursing Diagnosis", "reqd": 1},
			{"fieldname": "goals", "fieldtype": "Text", "label": "Goals"},
			{"fieldname": "interventions", "fieldtype": "Text", "label": "Interventions"},
			{"default": "Active", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nCompleted\nCancelled"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_discharge_summary", {
		"autoname": "format:DSM-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission", "reqd": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "encounter", "fieldtype": "Link", "label": "Encounter", "options": "Healthcare Encounter"},
			{"fieldname": "summary", "fieldtype": "Text Editor", "label": "Discharge Summary"},
			{"fieldname": "discharge_datetime", "fieldtype": "Datetime", "label": "Discharge Date/Time"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_eligibility_check", {
		"autoname": "format:ELG-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "payer", "fieldtype": "Link", "label": "Payer", "options": "Healthcare Payer", "reqd": 1},
			{"fieldname": "member_id", "fieldtype": "Data", "label": "Member ID"},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Eligible\nNot Eligible\nUnknown", "reqd": 1},
			{"fieldname": "copay_percent", "fieldtype": "Percent", "label": "Copay %"},
			{"fieldname": "response_payload", "fieldtype": "Code", "label": "Response JSON", "options": "JSON"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_nphies_claim_bundle", {
		"autoname": "format:NPH-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "insurance_claim", "fieldtype": "Link", "label": "Insurance Claim", "options": "Healthcare Insurance Claim", "reqd": 1},
			{"fieldname": "bundle_type", "fieldtype": "Select", "label": "Bundle Type", "options": "Claim\nEligibility\nPrior Auth", "reqd": 1},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nSubmitted\nAccepted\nRejected", "reqd": 1},
			{"fieldname": "fhir_bundle", "fieldtype": "Code", "label": "FHIR Bundle JSON", "options": "JSON"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_barcode_scan_log", {
		"autoname": "format:BCS-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "scan_context", "fieldtype": "Select", "label": "Context", "options": "eMAR\nPharmacy Dispense\nLab Sample", "reqd": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient"},
			{"fieldname": "barcode", "fieldtype": "Data", "label": "Barcode", "reqd": 1},
			{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item"},
			{"fieldname": "verified", "fieldtype": "Check", "label": "Verified", "default": "1"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_patient_push_notification", {
		"autoname": "format:PPN-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "channel", "fieldtype": "Select", "label": "Channel", "options": "Push\nSMS\nEmail", "reqd": 1},
			{"fieldname": "message", "fieldtype": "Small Text", "label": "Message", "reqd": 1},
			{"default": "Queued", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Queued\nSent\nFailed"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
		],
	}),
	("healthcare_clinical_ai_insight", {
		"autoname": "format:CAI-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "insight_type", "fieldtype": "Select", "label": "Type", "options": "Risk\nRecommendation\nSummary\nAlert", "reqd": 1},
			{"fieldname": "summary", "fieldtype": "Text", "label": "Summary", "reqd": 1},
			{"fieldname": "confidence", "fieldtype": "Percent", "label": "Confidence"},
			{"fieldname": "source", "fieldtype": "Data", "label": "Source Model"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_implant_trace", {
		"autoname": "format:IMP-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "surgical_case", "fieldtype": "Link", "label": "Surgical Case", "options": "Healthcare Surgical Case", "reqd": 1},
			{"fieldname": "udi", "fieldtype": "Data", "label": "UDI / GS1", "reqd": 1, "in_list_view": 1},
			{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item"},
			{"fieldname": "lot_number", "fieldtype": "Data", "label": "Lot"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
		],
	}),
	("healthcare_pre_op_checklist", {
		"autoname": "format:POC-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "surgical_case", "fieldtype": "Link", "label": "Surgical Case", "options": "Healthcare Surgical Case", "reqd": 1},
			{"fieldname": "site_marked", "fieldtype": "Check", "label": "Site Marked"},
			{"fieldname": "consent_signed", "fieldtype": "Check", "label": "Consent Signed"},
			{"fieldname": "antibiotics_given", "fieldtype": "Check", "label": "Antibiotics Prophylaxis"},
			{"fieldname": "who_checklist_complete", "fieldtype": "Check", "label": "WHO Checklist Complete"},
			{"default": "Pending", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Pending\nComplete"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
		],
	}),
	("healthcare_lis_instrument_message", {
		"autoname": "format:LIM-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "instrument_id", "fieldtype": "Data", "label": "Instrument ID", "reqd": 1},
			{"fieldname": "protocol", "fieldtype": "Select", "label": "Protocol", "options": "ASTM\nHL7", "reqd": 1},
			{"fieldname": "direction", "fieldtype": "Select", "label": "Direction", "options": "Inbound\nOutbound"},
			{"fieldname": "payload", "fieldtype": "Code", "label": "Message", "options": "JSON"},
			{"fieldname": "lab_sample", "fieldtype": "Link", "label": "Lab Sample", "options": "Healthcare Lab Sample"},
			{"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Received\nProcessed\nError", "reqd": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
		],
	}),
]


def class_name(folder: str) -> str:
	return "Healthcare" + "".join(p.capitalize() for p in folder.replace("healthcare_", "").split("_"))


def main():
	for folder, spec in SPECS:
		path = ROOT / folder
		path.mkdir(parents=True, exist_ok=True)
		parts = folder.replace("healthcare_", "").split("_")
		title = "Healthcare " + " ".join(p.capitalize() for p in parts)
		doc = {
			"actions": [],
			"doctype": "DocType",
			"engine": "InnoDB",
			"module": "Omnexa Healthcare",
			"name": title,
			"permissions": PERMS,
			"track_changes": 1,
			**{k: v for k, v in spec.items() if k not in ("fields", "istable")},
			"fields": spec["fields"],
		}
		(path / f"{folder}.json").write_text(json.dumps(doc, indent="\t") + "\n")
		py = path / f"{folder}.py"
		if not py.exists():
			cls = class_name(folder)
			py.write_text(
				f"# Copyright (c) 2026, Omnexa and contributors\n# License: MIT\nfrom frappe.model.document import Document\n\n\nclass {cls}(Document):\n\tpass\n"
			)
		init = path / "__init__.py"
		if not init.exists():
			init.write_text("")
	print(f"Scaffolded {len(SPECS)} epic-parity doctypes")


if __name__ == "__main__":
	main()
