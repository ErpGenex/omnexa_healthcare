#!/usr/bin/env python3
"""Scaffold Healthcare world-class DocTypes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "omnexa_healthcare" / "doctype"
PERMS = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
	{"role": "Company Admin", "read": 1, "write": 1, "create": 1, "delete": 0},
	{"role": "Desk User", "read": 1, "write": 1, "create": 1, "delete": 0},
]

SPECS = [
	("healthcare_icd10_code", {
		"autoname": "field:code",
		"fields": [
			{"fieldname": "code", "fieldtype": "Data", "label": "ICD-10 Code", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "description", "fieldtype": "Data", "label": "Description", "reqd": 1, "in_list_view": 1},
			{"fieldname": "chapter", "fieldtype": "Data", "label": "Chapter"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_lab_test_panel", {
		"autoname": "field:panel_code",
		"fields": [
			{"fieldname": "panel_code", "fieldtype": "Data", "label": "Panel Code", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "panel_name", "fieldtype": "Data", "label": "Panel Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "loinc_code", "fieldtype": "Data", "label": "LOINC Code"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "tests", "fieldtype": "Table", "label": "Tests", "options": "Healthcare Lab Test Panel Test"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_lab_test_panel_test", {
		"istable": 1,
		"fields": [
			{"fieldname": "test_name", "fieldtype": "Data", "label": "Test Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "loinc_code", "fieldtype": "Data", "label": "LOINC", "in_list_view": 1},
			{"fieldname": "unit", "fieldtype": "Data", "label": "Unit"},
		],
	}),
	("healthcare_lab_reference_range", {
		"autoname": "format:HLR-{#####}",
		"fields": [
			{"fieldname": "test_name", "fieldtype": "Data", "label": "Test Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "loinc_code", "fieldtype": "Data", "label": "LOINC Code"},
			{"fieldname": "gender", "fieldtype": "Select", "label": "Gender", "options": "\nMale\nFemale\nOther"},
			{"fieldname": "age_min", "fieldtype": "Int", "label": "Age Min"},
			{"fieldname": "age_max", "fieldtype": "Int", "label": "Age Max"},
			{"fieldname": "low_value", "fieldtype": "Float", "label": "Low"},
			{"fieldname": "high_value", "fieldtype": "Float", "label": "High"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
		],
	}),
	("healthcare_lab_qc_log", {
		"autoname": "format:HQC-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "qc_date", "fieldtype": "Date", "label": "QC Date", "reqd": 1, "in_list_view": 1},
			{"fieldname": "test_name", "fieldtype": "Data", "label": "Test / Control", "reqd": 1},
			{"fieldname": "result_value", "fieldtype": "Float", "label": "Result"},
			{"fieldname": "expected_range", "fieldtype": "Data", "label": "Expected Range"},
			{"fieldname": "in_control", "fieldtype": "Check", "label": "In Control", "default": "1"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
		],
	}),
	("healthcare_imaging_modality", {
		"autoname": "field:modality_code",
		"fields": [
			{"fieldname": "modality_code", "fieldtype": "Data", "label": "Modality Code", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "modality_name", "fieldtype": "Data", "label": "Modality Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "dicom_modality", "fieldtype": "Select", "label": "DICOM Modality", "options": "CT\nMR\nXR\nUS\nMG\nNM\nPT\nRF\nOT"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_radiology_report_template", {
		"autoname": "format:HRT-{#####}",
		"fields": [
			{"fieldname": "template_name", "fieldtype": "Data", "label": "Template Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "modality", "fieldtype": "Link", "label": "Modality", "options": "Healthcare Imaging Modality"},
			{"fieldname": "structured_body", "fieldtype": "Text Editor", "label": "Structured Body"},
			{"fieldname": "grading_system", "fieldtype": "Data", "label": "Grading System", "description": "e.g. BI-RADS, LI-RADS"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_drug_interaction_rule", {
		"autoname": "format:HDR-{#####}",
		"fields": [
			{"fieldname": "drug_a", "fieldtype": "Link", "label": "Drug A", "options": "Item", "reqd": 1, "in_list_view": 1},
			{"fieldname": "drug_b", "fieldtype": "Link", "label": "Drug B", "options": "Item", "reqd": 1, "in_list_view": 1},
			{"fieldname": "severity", "fieldtype": "Select", "label": "Severity", "options": "Minor\nModerate\nMajor\nContraindicated", "reqd": 1, "in_list_view": 1},
			{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_ward_requisition", {
		"autoname": "format:HWR-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "requisition_date", "fieldtype": "Date", "label": "Requisition Date", "reqd": 1, "default": "Today", "in_list_view": 1},
			{"fieldname": "ward_service_unit", "fieldtype": "Link", "label": "Ward", "options": "Healthcare Service Unit", "reqd": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
			{"fieldname": "items", "fieldtype": "Table", "label": "Items", "options": "Healthcare Ward Requisition Item"},
			{"default": "Draft", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nSubmitted\nIssued\nCancelled", "reqd": 1, "in_list_view": 1},
			{"fieldname": "stock_entry", "fieldtype": "Link", "label": "Stock Entry", "options": "Stock Entry", "read_only": 1},
		],
	}),
	("healthcare_ward_requisition_item", {
		"istable": 1,
		"fields": [
			{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item", "reqd": 1, "in_list_view": 1},
			{"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "reqd": 1, "default": "1"},
			{"fieldname": "uom", "fieldtype": "Link", "label": "UOM", "options": "UOM"},
		],
	}),
	("healthcare_ot_consumable_issue", {
		"autoname": "format:HOT-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "issue_date", "fieldtype": "Date", "label": "Issue Date", "reqd": 1, "default": "Today", "in_list_view": 1},
			{"fieldname": "surgical_case", "fieldtype": "Link", "label": "Surgical Case", "options": "Healthcare Surgical Case"},
			{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item", "reqd": 1, "in_list_view": 1},
			{"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "reqd": 1, "default": "1"},
			{"fieldname": "warehouse", "fieldtype": "Link", "label": "Warehouse", "options": "Warehouse"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
			{"fieldname": "stock_entry", "fieldtype": "Link", "label": "Stock Entry", "options": "Stock Entry", "read_only": 1},
		],
	}),
	("healthcare_item_par_level", {
		"autoname": "format:HIP-{#####}",
		"fields": [
			{"fieldname": "item", "fieldtype": "Link", "label": "Item", "options": "Item", "reqd": 1, "in_list_view": 1},
			{"fieldname": "warehouse", "fieldtype": "Link", "label": "Warehouse", "options": "Warehouse", "reqd": 1, "in_list_view": 1},
			{"fieldname": "par_level", "fieldtype": "Float", "label": "Par Level", "reqd": 1},
			{"fieldname": "reorder_qty", "fieldtype": "Float", "label": "Reorder Qty"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_prior_authorization", {
		"autoname": "format:HPA-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "payer", "fieldtype": "Link", "label": "Payer", "options": "Healthcare Payer", "reqd": 1},
			{"fieldname": "insurance_plan", "fieldtype": "Link", "label": "Insurance Plan", "options": "Healthcare Insurance Plan"},
			{"fieldname": "service_description", "fieldtype": "Data", "label": "Service", "reqd": 1},
			{"fieldname": "auth_number", "fieldtype": "Data", "label": "Authorization Number"},
			{"default": "Draft", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nSubmitted\nPending\nApproved\nDenied\nExpired", "reqd": 1, "in_list_view": 1},
			{"fieldname": "valid_from", "fieldtype": "Date", "label": "Valid From"},
			{"fieldname": "valid_to", "fieldtype": "Date", "label": "Valid To"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_claim_remittance", {
		"autoname": "format:HCR-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "insurance_claim", "fieldtype": "Link", "label": "Insurance Claim", "options": "Healthcare Insurance Claim", "reqd": 1, "in_list_view": 1},
			{"fieldname": "remittance_date", "fieldtype": "Date", "label": "Remittance Date", "reqd": 1},
			{"fieldname": "paid_amount", "fieldtype": "Currency", "label": "Paid Amount", "reqd": 1},
			{"fieldname": "adjustment_amount", "fieldtype": "Currency", "label": "Adjustment"},
			{"fieldname": "reference_number", "fieldtype": "Data", "label": "EOB / Reference"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_patient_merge_log", {
		"autoname": "format:HPM-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "source_patient", "fieldtype": "Link", "label": "Source Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "target_patient", "fieldtype": "Link", "label": "Target Patient", "options": "Healthcare Patient", "reqd": 1},
			{"fieldname": "merged_by", "fieldtype": "Link", "label": "Merged By", "options": "User"},
			{"fieldname": "merged_on", "fieldtype": "Datetime", "label": "Merged On"},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
		],
	}),
	("healthcare_phi_access_log", {
		"autoname": "format:HPH-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "user", "fieldtype": "Link", "label": "User", "options": "User", "reqd": 1, "in_list_view": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "in_list_view": 1},
			{"fieldname": "reference_doctype", "fieldtype": "Data", "label": "DocType", "reqd": 1},
			{"fieldname": "reference_name", "fieldtype": "Data", "label": "Document", "reqd": 1},
			{"fieldname": "action", "fieldtype": "Select", "label": "Action", "options": "Read\nWrite\nExport\nPrint", "reqd": 1},
			{"fieldname": "accessed_on", "fieldtype": "Datetime", "label": "Accessed On", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_patient_consent", {
		"autoname": "format:HPC-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "consent_type", "fieldtype": "Select", "label": "Consent Type", "options": "Treatment\nData Sharing\nResearch\nMarketing", "reqd": 1},
			{"fieldname": "consent_given", "fieldtype": "Check", "label": "Consent Given", "default": "0"},
			{"fieldname": "signed_on", "fieldtype": "Datetime", "label": "Signed On"},
			{"fieldname": "witness", "fieldtype": "Link", "label": "Witness", "options": "User"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
		],
	}),
	("healthcare_nursing_observation_chart", {
		"autoname": "format:HNO-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission"},
			{"fieldname": "observation_type", "fieldtype": "Select", "label": "Type", "options": "Vitals\nIntake/Output\nPain\nNeuro\nOther", "reqd": 1, "in_list_view": 1},
			{"fieldname": "observation_datetime", "fieldtype": "Datetime", "label": "Observed At", "reqd": 1},
			{"fieldname": "value_json", "fieldtype": "JSON", "label": "Values"},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			{"fieldname": "recorded_by", "fieldtype": "Link", "label": "Recorded By", "options": "User"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_medication_administration_record", {
		"autoname": "format:HMA-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "admission", "fieldtype": "Link", "label": "Admission", "options": "Healthcare Admission"},
			{"fieldname": "medication_statement", "fieldtype": "Link", "label": "Medication Order", "options": "Healthcare Medication Statement"},
			{"fieldname": "item", "fieldtype": "Link", "label": "Drug", "options": "Item", "reqd": 1},
			{"fieldname": "scheduled_time", "fieldtype": "Datetime", "label": "Scheduled Time", "reqd": 1, "in_list_view": 1},
			{"fieldname": "administered_time", "fieldtype": "Datetime", "label": "Administered At"},
			{"default": "Scheduled", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Scheduled\nGiven\nHeld\nRefused\nMissed", "reqd": 1, "in_list_view": 1},
			{"fieldname": "dose", "fieldtype": "Data", "label": "Dose"},
			{"fieldname": "nurse", "fieldtype": "Link", "label": "Nurse", "options": "User"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
	("healthcare_surgical_team_member", {
		"istable": 1,
		"fields": [
			{"fieldname": "practitioner", "fieldtype": "Link", "label": "Practitioner", "options": "Healthcare Practitioner", "reqd": 1, "in_list_view": 1},
			{"fieldname": "role", "fieldtype": "Select", "label": "Role", "options": "Primary Surgeon\nAssistant\nAnesthesiologist\nScrub Nurse\nCirculating Nurse", "reqd": 1},
		],
	}),
	("healthcare_anesthesia_record", {
		"autoname": "format:HAR-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "surgical_case", "fieldtype": "Link", "label": "Surgical Case", "options": "Healthcare Surgical Case", "reqd": 1, "in_list_view": 1},
			{"fieldname": "anesthesiologist", "fieldtype": "Link", "label": "Anesthesiologist", "options": "Healthcare Practitioner"},
			{"fieldname": "asa_class", "fieldtype": "Select", "label": "ASA Class", "options": "I\nII\nIII\nIV\nV\nVI"},
			{"fieldname": "anesthesia_type", "fieldtype": "Select", "label": "Anesthesia Type", "options": "General\nRegional\nLocal\nSedation"},
			{"fieldname": "start_time", "fieldtype": "Datetime", "label": "Start"},
			{"fieldname": "end_time", "fieldtype": "Datetime", "label": "End"},
			{"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch", "reqd": 1},
		],
	}),
]


def class_name(dt: str) -> str:
	return "".join(p.capitalize() for p in dt.replace("healthcare_", "").split("_"))


def main():
	for folder, spec in SPECS:
		path = ROOT / folder
		path.mkdir(parents=True, exist_ok=True)
		name = " ".join(w.capitalize() for w in folder.replace("healthcare_", "").split("_"))
		name = "Healthcare " + name if not name.startswith("Healthcare") else name
		# fix naming
		parts = folder.replace("healthcare_", "").split("_")
		title = "Healthcare " + " ".join(p.capitalize() for p in parts)
		doc = {
			"actions": [],
			"doctype": "DocType",
			"engine": "InnoDB",
			"module": "Omnexa Healthcare",
			"name": title,
			"permissions": PERMS if not spec.get("istable") else [],
			"track_changes": 1,
			**{k: v for k, v in spec.items() if k not in ("fields", "istable")},
			"fields": spec["fields"],
		}
		if spec.get("istable"):
			doc["istable"] = 1
			doc.pop("permissions", None)
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
	print(f"Scaffolded {len(SPECS)} doctypes")


if __name__ == "__main__":
	main()
