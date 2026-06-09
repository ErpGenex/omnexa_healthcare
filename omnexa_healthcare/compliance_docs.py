# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""JCI / ISO 15189 compliance documentation index."""

from __future__ import annotations

import frappe

COMPLIANCE_DOCS = {
	"jci": {
		"title": "JCI Hospital Information System Mapping",
		"version": "2026.06",
		"sections": {
			"International Patient Safety Goals": [
				"Patient identification via Healthcare Patient Identifier (MRN).",
				"Medication safety via Healthcare Drug Interaction Rule and MAR.",
				"Procedure site verification via Healthcare Surgical Case OR booking.",
			],
			"Medication Management": [
				"Healthcare Medication Statement for active medications.",
				"Healthcare Medication Administration Record for inpatient administration.",
				"Healthcare Medication Dispense with FEFO batch selection.",
			],
			"Patient Care Records": [
				"FHIR Encounter export and structured clinical templates per specialty.",
				"Healthcare Phi Access Log for audit trail on sensitive reads.",
			],
			"Surgical Care": [
				"Healthcare Operating Room status and conflict validation.",
				"Healthcare Anesthesia Record auto-created when case starts.",
				"Healthcare Surgical Team Member roles including Anesthesiologist.",
			],
		},
	},
	"iso_15189": {
		"title": "ISO 15189 Laboratory QMS Guide",
		"version": "2026.06",
		"sections": {
			"Pre-analytical phase": [
				"Healthcare Lab Sample collection and rejection tracking.",
				"Healthcare Service Request for lab orders with panels.",
			],
			"Analytical phase": [
				"Healthcare Diagnostic Report with abnormal_flag and structured_template.",
				"Healthcare Lab QC Log for QC documentation.",
			],
			"Post-analytical phase": [
				"Healthcare Lab Workbench page for result entry.",
				"Reports: Lab TAT, Rejection Rate, Abnormal Results.",
			],
			"QC documentation": [
				"Healthcare Lab QC Log DocType linked from compliance matrix.",
				"Executive dashboard for operational KPI monitoring.",
			],
		},
	},
}


@frappe.whitelist()
def get_compliance_documentation():
	return COMPLIANCE_DOCS
