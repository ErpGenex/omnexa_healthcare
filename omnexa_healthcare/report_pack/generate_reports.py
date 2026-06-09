#!/usr/bin/env python3
"""Generate Healthcare operational report pack (run from bench root)."""

from __future__ import annotations

import json
from pathlib import Path

REPORT_ROOT = Path(__file__).resolve().parents[1] / "omnexa_healthcare" / "report"

REPORTS: list[dict] = [
	# Scheduling
	{"folder": "healthcare_appointment_by_department", "title": "Healthcare Appointment By Department", "ref": "Healthcare Appointment", "group": "department", "count": "appointments"},
	{"folder": "healthcare_appointment_by_specialty", "title": "Healthcare Appointment By Specialty", "ref": "Healthcare Appointment", "group": "specialty", "count": "appointments"},
	{"folder": "healthcare_appointment_cancelled_summary", "title": "Healthcare Appointment Cancelled Summary", "ref": "Healthcare Appointment", "status": "Cancelled"},
	{"folder": "healthcare_telehealth_appointments", "title": "Healthcare Telehealth Appointments", "ref": "Healthcare Appointment", "type": "Telehealth"},
	{"folder": "healthcare_appointment_lead_time", "title": "Healthcare Appointment Lead Time", "ref": "Healthcare Appointment", "metric": "lead_time"},
	{"folder": "healthcare_practitioner_roster_summary", "title": "Healthcare Practitioner Roster Summary", "ref": "Healthcare Practitioner", "metric": "roster"},
	# Financial / RCM
	{"folder": "healthcare_insurance_claim_summary", "title": "Healthcare Insurance Claim Summary", "ref": "Healthcare Insurance Claim", "table": "Healthcare Insurance Claim"},
	{"folder": "healthcare_patient_copay_summary", "title": "Healthcare Patient Copay Summary", "ref": "Healthcare Patient Coverage", "table": "Healthcare Patient Coverage"},
	{"folder": "healthcare_unpaid_booking_fees", "title": "Healthcare Unpaid Booking Fees", "ref": "Healthcare Appointment", "metric": "unpaid_fees"},
	{"folder": "healthcare_procedure_revenue", "title": "Healthcare Procedure Revenue", "ref": "Healthcare Procedure Order", "table": "Healthcare Procedure Order"},
	{"folder": "healthcare_payer_aging", "title": "Healthcare Payer Aging", "ref": "Healthcare Insurance Claim", "metric": "payer_aging"},
	{"folder": "healthcare_daily_cash_collection", "title": "Healthcare Daily Cash Collection", "ref": "Healthcare Service Charge", "metric": "daily_cash"},
	{"folder": "healthcare_service_charge_by_patient", "title": "Healthcare Service Charge By Patient", "ref": "Healthcare Service Charge", "group": "patient"},
	{"folder": "healthcare_prior_auth_pending", "title": "Healthcare Prior Auth Pending", "ref": "Healthcare Prior Authorization", "table": "Healthcare Prior Authorization"},
	# Clinical
	{"folder": "healthcare_encounter_by_practitioner", "title": "Healthcare Encounter By Practitioner", "ref": "Healthcare Encounter", "group": "practitioner"},
	{"folder": "healthcare_diagnosis_frequency", "title": "Healthcare Diagnosis Frequency", "ref": "Healthcare Encounter Diagnosis", "table": "Healthcare Encounter Diagnosis"},
	{"folder": "healthcare_allergy_patient_list", "title": "Healthcare Allergy Patient List", "ref": "Healthcare Allergy Intolerance", "table": "Healthcare Allergy Intolerance"},
	{"folder": "healthcare_immunization_coverage", "title": "Healthcare Immunization Coverage", "ref": "Healthcare Immunization", "table": "Healthcare Immunization"},
	{"folder": "healthcare_episode_duration", "title": "Healthcare Episode Duration", "ref": "Healthcare Episode Of Care", "table": "Healthcare Episode Of Care"},
	{"folder": "healthcare_clinical_template_usage", "title": "Healthcare Clinical Template Usage", "ref": "Healthcare Clinical Template", "table": "Healthcare Clinical Template"},
	# Lab
	{"folder": "healthcare_lab_tat_analysis", "title": "Healthcare Lab TAT Analysis", "ref": "Healthcare Lab Sample", "metric": "lab_tat"},
	{"folder": "healthcare_pending_lab_samples", "title": "Healthcare Pending Lab Samples", "ref": "Healthcare Lab Sample", "status": "in_lab"},
	{"folder": "healthcare_lab_rejection_rate", "title": "Healthcare Lab Rejection Rate", "ref": "Healthcare Lab Sample", "status": "rejected"},
	{"folder": "healthcare_lab_panel_volume", "title": "Healthcare Lab Panel Volume", "ref": "Healthcare Lab Test Panel", "table": "Healthcare Lab Test Panel"},
	{"folder": "healthcare_abnormal_lab_results", "title": "Healthcare Abnormal Lab Results", "ref": "Healthcare Diagnostic Report", "metric": "abnormal"},
	# Radiology
	{"folder": "healthcare_radiology_tat", "title": "Healthcare Radiology TAT", "ref": "Healthcare Service Request", "metric": "rad_tat"},
	{"folder": "healthcare_radiology_by_modality", "title": "Healthcare Radiology By Modality", "ref": "Healthcare Service Request", "group": "modality"},
	{"folder": "healthcare_pending_imaging_orders", "title": "Healthcare Pending Imaging Orders", "ref": "Healthcare Service Request", "category": "imaging"},
	{"folder": "healthcare_structured_report_usage", "title": "Healthcare Structured Report Usage", "ref": "Healthcare Radiology Report Template", "table": "Healthcare Radiology Report Template"},
	# Pharmacy
	{"folder": "healthcare_dispense_summary", "title": "Healthcare Dispense Summary", "ref": "Healthcare Medication Dispense", "table": "Healthcare Medication Dispense"},
	{"folder": "healthcare_drug_interaction_alerts", "title": "Healthcare Drug Interaction Alerts", "ref": "Healthcare Drug Interaction Rule", "table": "Healthcare Drug Interaction Rule"},
	{"folder": "healthcare_pharmacy_stock_below_par", "title": "Healthcare Pharmacy Stock Below Par", "ref": "Healthcare Item Par Level", "table": "Healthcare Item Par Level"},
	# IPD / OT
	{"folder": "healthcare_or_utilization", "title": "Healthcare OR Utilization", "ref": "Healthcare Surgical Case", "table": "Healthcare Surgical Case"},
	{"folder": "healthcare_icu_occupancy", "title": "Healthcare ICU Occupancy", "ref": "Healthcare Bed", "bed_type": "ICU"},
	{"folder": "healthcare_mar_compliance", "title": "Healthcare MAR Compliance", "ref": "Healthcare Medication Administration Record", "table": "Healthcare Medication Administration Record"},
	{"folder": "healthcare_nursing_observation_summary", "title": "Healthcare Nursing Observation Summary", "ref": "Healthcare Nursing Observation Chart", "table": "Healthcare Nursing Observation Chart"},
	# Inventory
	{"folder": "healthcare_ward_requisition_status", "title": "Healthcare Ward Requisition Status", "ref": "Healthcare Ward Requisition", "table": "Healthcare Ward Requisition"},
	{"folder": "healthcare_ot_consumable_usage", "title": "Healthcare OT Consumable Usage", "ref": "Healthcare OT Consumable Issue", "table": "Healthcare OT Consumable Issue"},
]

PY_TEMPLATE = '''# Auto-generated Healthcare report pack
import frappe
from frappe import _
from omnexa_healthcare.report_pack._helpers import branch_conditions, date_conditions, require_company
from omnexa_healthcare.report_pack.executors import run_report


def execute(filters=None):
\treturn run_report("{folder}", filters)
'''

JSON_TEMPLATE = {
	"add_total_row": 1,
	"columns": [],
	"disabled": 0,
	"doctype": "Report",
	"is_standard": "Yes",
	"module": "Omnexa Healthcare",
	"prepared_report": 0,
	"report_type": "Script Report",
	"roles": [{"role": r} for r in ["System Manager", "Company Admin", "Desk User", "Report Manager", "Physician", "Nursing User"]],
}


def main():
	REPORT_ROOT.mkdir(parents=True, exist_ok=True)
	for spec in REPORTS:
		folder = spec["folder"]
		path = REPORT_ROOT / folder
		path.mkdir(parents=True, exist_ok=True)
		py_file = path / f"{folder}.py"
		if not py_file.exists():
			py_file.write_text(PY_TEMPLATE.format(folder=folder))
		json_file = path / f"{folder}.json"
		if not json_file.exists():
			data = dict(JSON_TEMPLATE)
			data["name"] = spec["title"]
			data["report_name"] = spec["title"]
			data["ref_doctype"] = spec["ref"]
			data["filters"] = JSON_TEMPLATE.get("filters") or [
				{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
				{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
				{"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1},
				{"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1},
			]
			json_file.write_text(json.dumps(data, indent=1) + "\n")
	print(f"Generated/verified {len(REPORTS)} reports under {REPORT_ROOT}")


if __name__ == "__main__":
	main()
