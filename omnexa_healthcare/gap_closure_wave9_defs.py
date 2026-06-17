# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Wave 9 — Compliance & security DocTypes."""

from __future__ import annotations

GAP_CLOSURE_WAVE9_DOCTYPES: list[dict] = [
	{
		"name": "Healthcare Patient Erasure Request",
		"is_submittable": True,
		"autoname": "naming_series:",
		"naming_series": "PER-.#####",
		"fields": [
			("naming_series", "Select", "Series", {"options": "PER-.#####", "reqd": 1, "default": "PER-.#####"}),
			("patient", "Link", "Patient", {"options": "Healthcare Patient", "reqd": 1, "in_list_view": 1}),
			("request_type", "Select", "Request type", {"options": "Erasure\nRestriction\nPortability", "default": "Erasure", "reqd": 1}),
			("status", "Select", "Status", {"options": "Draft\nSubmitted\nIn Review\nCompleted\nRejected", "default": "Draft", "in_list_view": 1}),
			("requested_by", "Link", "Requested by", {"options": "User"}),
			("requested_on", "Datetime", "Requested on", {"default": "Now"}),
			("completed_on", "Datetime", "Completed on"),
			("notes", "Text", "Notes"),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch", "reqd": 1}),
		],
	},
]

PHI_AUDIT_DOCTYPES: list[str] = [
	"Healthcare Patient",
	"Healthcare Encounter",
	"Healthcare Appointment",
	"Healthcare Diagnostic Report",
	"Healthcare Medication Statement",
	"Healthcare Medication Request",
	"Healthcare Allergy Intolerance",
	"Healthcare Clinical Condition",
	"Healthcare Observation",
	"Healthcare Immunization",
	"Healthcare Service Request",
	"Healthcare Lab Sample",
	"Healthcare Admission",
	"Healthcare Insurance Claim",
	"Healthcare Patient Coverage",
	"Healthcare Prior Authorization",
	"Healthcare Family Unit",
	"Healthcare Family History",
	"Healthcare Preventive Care Plan",
	"Healthcare Family Risk Score",
	"Healthcare Blood Unit",
	"Healthcare Transfusion Order",
	"Healthcare Er Visit",
	"Healthcare Nursing Care Plan",
	"Healthcare Discharge Summary",
	"Healthcare Patient Consent",
	"Healthcare Secure Message",
]
