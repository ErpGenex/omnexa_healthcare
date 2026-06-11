# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""JCI / ISO 15189 compliance documentation index."""

from __future__ import annotations

import frappe

COMPLIANCE_DOCS = {
	"hipaa": {
		"title": "HIPAA Security & Privacy Rule Mapping",
		"version": "2026.06",
		"sections": {
			"Administrative Safeguards": [
				"Healthcare Phi Access Log for minimum necessary access reviews.",
				"Healthcare Patient Consent for treatment and data sharing.",
				"MFA enforcement for PHI clinical roles (Healthcare Settings).",
			],
			"Technical Safeguards": [
				"Branch-scoped permission_query_conditions on 26+ clinical DocTypes.",
				"PHI audit logging on Patient and Encounter doc_events.",
				"License gate and guest API restrictions on web booking.",
			],
			"Breach Notification": [
				"Healthcare Phi Access Log export for incident response.",
				"Change ticket and policy reference on Healthcare Settings.",
			],
		},
	},
	"gdpr": {
		"title": "GDPR Healthcare Data Protection Guide",
		"version": "2026.06",
		"sections": {
			"Lawful Basis & Consent": [
				"Healthcare Patient Consent DocType with consent type and signed timestamp.",
				"Patient right to restrict secondary use (consent flags).",
			],
			"Data Subject Rights": [
				"Healthcare Patient Merge Log for identity resolution.",
				"FHIR export for portable patient summary (IPS bundle).",
			],
			"Security of Processing": [
				"MFA for clinical roles, PHI audit trail, encryption at rest (platform).",
			],
		},
	},
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
	"himss_emram": {
		"title": "HIMSS EMRAM Stage 6 Evidence Pack",
		"version": "2026.06",
		"sections": {
			"Stage 6 — Data analytics": [
				"Healthcare Executive Dashboard and 48 operational reports.",
				"Predictive analytics: occupancy forecast and readmission risk APIs.",
				"Population health cohorts and specialty revenue analytics.",
			],
			"Closed loop medication": [
				"Healthcare Drug Interaction Rule and eMAR administration records.",
				"Pharmacy dispensing desk with FEFO batch traceability.",
			],
			"Patient engagement": [
				"Consumer patient SPA, OTP, online payments, telehealth video.",
				"Hospital public website /hospital and activity portal routing.",
			],
			"Certification tracking": [
				"Healthcare Certification Record DocType with HIMSS EMRAM stage.",
			],
		},
	},
	"jci_digital": {
		"title": "JCI Digital Accreditation Readiness",
		"version": "2026.06",
		"sections": {
			"Patient safety": [
				"MRN identification, medication safety, surgical case verification.",
				"Nursing incident reporting and shift handover workflows.",
			],
			"Clinical records": [
				"FHIR Encounter export, PHI audit log, structured specialty templates.",
			],
			"Quality & performance": [
				"Load test report for 500+ bed scale validation.",
				"DR runbook tested and penetration test evidence.",
			],
			"Certification": [
				"Healthcare Certification Record — JCI Digital accreditation ready.",
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
