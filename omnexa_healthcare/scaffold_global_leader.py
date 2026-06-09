#!/usr/bin/env python3
"""Scaffold Global Leader DocTypes — cohorts, messaging, AI, DRG, mobile, X12."""

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
	{"role": "Patient Portal User", "read": 1, "write": 1, "create": 1, "delete": 0},
]

SPECS = [
	("healthcare_patient_cohort", {
		"autoname": "format:COH-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "cohort_name", "fieldtype": "Data", "label": "Cohort Name", "reqd": 1, "in_list_view": 1},
			{"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
			{"fieldname": "criteria_json", "fieldtype": "Code", "label": "Criteria JSON", "options": "JSON"},
			{"default": "Active", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Active\nArchived", "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_care_gap", {
		"autoname": "format:GAP-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "cohort", "fieldtype": "Link", "label": "Cohort", "options": "Healthcare Patient Cohort"},
			{"fieldname": "gap_type", "fieldtype": "Select", "label": "Gap Type", "options": "Screening\nImmunization\nChronic Care\nFollow-up\nMedication Adherence", "reqd": 1, "in_list_view": 1},
			{"fieldname": "description", "fieldtype": "Small Text", "label": "Description", "reqd": 1},
			{"default": "Open", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Open\nClosed\nOverdue", "in_list_view": 1},
			{"fieldname": "due_date", "fieldtype": "Date", "label": "Due Date"},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_secure_message", {
		"autoname": "format:MSG-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "sender", "fieldtype": "Link", "label": "Sender", "options": "User", "reqd": 1},
			{"fieldname": "recipient", "fieldtype": "Link", "label": "Recipient", "options": "User", "reqd": 1, "in_list_view": 1},
			{"fieldname": "subject", "fieldtype": "Data", "label": "Subject"},
			{"fieldname": "body", "fieldtype": "Text", "label": "Message", "reqd": 1},
			{"default": "0", "fieldname": "is_read", "fieldtype": "Check", "label": "Read"},
			{"fieldname": "thread_id", "fieldtype": "Data", "label": "Thread ID", "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_ambient_session", {
		"autoname": "format:AMB-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "encounter", "fieldtype": "Link", "label": "Encounter", "options": "Healthcare Encounter"},
			{"fieldname": "practitioner", "fieldtype": "Link", "label": "Practitioner", "options": "Healthcare Practitioner"},
			{"fieldname": "transcript", "fieldtype": "Text", "label": "Transcript"},
			{"fieldname": "draft_note", "fieldtype": "Text Editor", "label": "Draft Clinical Note"},
			{"default": "Recording", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Recording\nProcessing\nReview\nFinalized", "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_voice_dictation", {
		"autoname": "format:DIC-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient", "reqd": 1, "in_list_view": 1},
			{"fieldname": "encounter", "fieldtype": "Link", "label": "Encounter", "options": "Healthcare Encounter"},
			{"fieldname": "dictated_by", "fieldtype": "Link", "label": "Dictated By", "options": "User", "reqd": 1},
			{"fieldname": "transcript", "fieldtype": "Text", "label": "Transcript", "reqd": 1},
			{"fieldname": "structured_note", "fieldtype": "Text Editor", "label": "Structured Note"},
			{"default": "Draft", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nSigned", "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
		],
	}),
	("healthcare_drg_code", {
		"autoname": "field:drg_code",
		"fields": [
			{"fieldname": "drg_code", "fieldtype": "Data", "label": "DRG Code", "reqd": 1, "unique": 1, "in_list_view": 1},
			{"fieldname": "description", "fieldtype": "Data", "label": "Description", "reqd": 1, "in_list_view": 1},
			{"fieldname": "weight", "fieldtype": "Float", "label": "Relative Weight"},
			{"fieldname": "base_rate", "fieldtype": "Currency", "label": "Base Rate"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_mobile_device_token", {
		"autoname": "format:MDT-{#####}",
		"fields": [
			{"fieldname": "user", "fieldtype": "Link", "label": "User", "options": "User", "reqd": 1, "in_list_view": 1},
			{"fieldname": "device_id", "fieldtype": "Data", "label": "Device ID", "reqd": 1, "in_list_view": 1},
			{"fieldname": "platform", "fieldtype": "Select", "label": "Platform", "options": "iOS\nAndroid\nWeb", "reqd": 1},
			{"fieldname": "push_token", "fieldtype": "Data", "label": "Push Token"},
			{"default": "1", "fieldname": "is_active", "fieldtype": "Check", "label": "Active"},
		],
	}),
	("healthcare_x12_transaction", {
		"autoname": "format:X12-{YYYY}-{#####}",
		"fields": [
			{"fieldname": "transaction_type", "fieldtype": "Select", "label": "Type", "options": "270\n271\n837\n835", "reqd": 1, "in_list_view": 1},
			{"fieldname": "direction", "fieldtype": "Select", "label": "Direction", "options": "Outbound\nInbound", "reqd": 1},
			{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Healthcare Patient"},
			{"fieldname": "insurance_claim", "fieldtype": "Link", "label": "Insurance Claim", "options": "Healthcare Insurance Claim"},
			{"fieldname": "payload", "fieldtype": "Code", "label": "X12 Payload", "options": "X12"},
			{"default": "Draft", "fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nSent\nAcknowledged\nRejected", "in_list_view": 1},
			{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
			{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
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
	print(f"Scaffolded {len(SPECS)} global-leader doctypes")


if __name__ == "__main__":
	main()
