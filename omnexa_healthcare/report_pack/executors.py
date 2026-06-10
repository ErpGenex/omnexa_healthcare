# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Central dispatcher for Healthcare operational report pack."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from omnexa_healthcare.report_pack._helpers import branch_conditions, date_conditions, require_company
from omnexa_core.omnexa_core.branch_access import get_allowed_branches

REPORT_SPECS: dict[str, dict] = {
	"healthcare_appointment_by_department": {"table": "Healthcare Appointment", "group": "department", "date": "appointment_date"},
	"healthcare_appointment_by_specialty": {"table": "Healthcare Appointment", "group": "specialty", "date": "appointment_date"},
	"healthcare_appointment_cancelled_summary": {"table": "Healthcare Appointment", "group": "status", "date": "appointment_date", "extra": "status = 'Cancelled'"},
	"healthcare_telehealth_appointments": {"table": "Healthcare Appointment", "group": "practitioner", "date": "appointment_date", "extra": "appointment_type = 'Telehealth'"},
	"healthcare_appointment_lead_time": {"metric": "lead_time"},
	"healthcare_practitioner_roster_summary": {"table": "Healthcare Practitioner", "group": "company", "no_date": True},
	"healthcare_insurance_claim_summary": {"table": "Healthcare Insurance Claim", "group": "status", "date": "creation"},
	"healthcare_patient_copay_summary": {"table": "Healthcare Patient Coverage", "group": "insurance_plan", "no_date": True},
	"healthcare_unpaid_booking_fees": {"table": "Healthcare Appointment", "group": "branch", "date": "appointment_date", "extra": "payment_status = 'Unpaid' AND booking_fee > 0"},
	"healthcare_procedure_revenue": {"table": "Healthcare Procedure Order", "group": "procedure", "date": "planned_date"},
	"healthcare_payer_aging": {"table": "Healthcare Insurance Claim", "group": "payer", "date": "creation", "extra": "status NOT IN ('Paid', 'Rejected')"},
	"healthcare_daily_cash_collection": {"table": "Healthcare Service Charge", "group": "posting_date", "date": "posting_date"},
	"healthcare_service_charge_by_patient": {"table": "Healthcare Service Charge", "group": "patient", "date": "posting_date"},
	"healthcare_prior_auth_pending": {"table": "Healthcare Prior Authorization", "group": "status", "date": "creation", "extra": "status IN ('Draft', 'Submitted', 'Pending')"},
	"healthcare_encounter_by_practitioner": {"table": "Healthcare Encounter", "group": "practitioner", "date": "period_start"},
	"healthcare_diagnosis_frequency": {"table": "Healthcare Encounter Diagnosis", "group": "icd10_code", "no_date": True, "no_branch": True},
	"healthcare_allergy_patient_list": {"table": "Healthcare Allergy Intolerance", "group": "patient", "no_date": True},
	"healthcare_immunization_coverage": {"table": "Healthcare Immunization", "group": "vaccine_name", "date": "occurrence_datetime"},
	"healthcare_episode_duration": {"table": "Healthcare Episode Of Care", "group": "status", "no_date": True},
	"healthcare_clinical_template_usage": {"table": "Healthcare Clinical Template", "group": "specialty", "no_date": True},
	"healthcare_lab_tat_analysis": {"metric": "lab_tat"},
	"healthcare_pending_lab_samples": {"table": "Healthcare Lab Sample", "group": "status", "date": "collected_datetime", "extra": "status IN ('planned', 'collected', 'in_lab')"},
	"healthcare_lab_rejection_rate": {"table": "Healthcare Lab Sample", "group": "branch", "date": "collected_datetime", "extra": "status = 'rejected'"},
	"healthcare_lab_panel_volume": {"table": "Healthcare Lab Test Panel", "group": "panel_name", "no_date": True},
	"healthcare_abnormal_lab_results": {"metric": "abnormal_lab"},
	"healthcare_radiology_tat": {"metric": "rad_tat"},
	"healthcare_radiology_by_modality": {"table": "Healthcare Service Request", "group": "modality", "date": "authored_on", "extra": "request_category = 'imaging'"},
	"healthcare_pending_imaging_orders": {"table": "Healthcare Service Request", "group": "status", "date": "authored_on", "extra": "request_category = 'imaging' AND status NOT IN ('completed', 'cancelled')"},
	"healthcare_structured_report_usage": {"table": "Healthcare Radiology Report Template", "group": "modality", "no_date": True},
	"healthcare_dispense_summary": {"table": "Healthcare Medication Dispense", "group": "status", "date": "dispensed_datetime"},
	"healthcare_drug_interaction_alerts": {"table": "Healthcare Drug Interaction Rule", "group": "severity", "no_date": True},
	"healthcare_pharmacy_stock_below_par": {"metric": "below_par"},
	"healthcare_or_utilization": {"table": "Healthcare Surgical Case", "group": "operating_room", "date": "scheduled_start"},
	"healthcare_icu_occupancy": {
		"table": "Healthcare Bed",
		"group": "status",
		"no_date": True,
		"extra": "bed_type IN ('ICU', 'HDU', 'NICU', 'Nursery')",
	},
	"healthcare_mar_compliance": {"table": "Healthcare Medication Administration Record", "group": "status", "date": "scheduled_time"},
	"healthcare_nursing_observation_summary": {"table": "Healthcare Nursing Observation Chart", "group": "observation_type", "date": "observation_datetime"},
	"healthcare_ward_requisition_status": {"table": "Healthcare Ward Requisition", "group": "status", "date": "requisition_date"},
	"healthcare_ot_consumable_usage": {"table": "Healthcare Ot Consumable Issue", "group": "item", "date": "issue_date"},
}


def run_report(report_key: str, filters=None):
	spec = REPORT_SPECS.get(report_key)
	if not spec:
		frappe.throw(_("Unknown report: {0}").format(report_key))
	filters = require_company(filters)
	metric = spec.get("metric")
	if metric == "lead_time":
		return _lead_time_report(filters)
	if metric == "lab_tat":
		return _lab_tat_report(filters)
	if metric == "abnormal_lab":
		return _abnormal_lab_report(filters)
	if metric == "rad_tat":
		return _rad_tat_report(filters)
	if metric == "below_par":
		return _below_par_report(filters)
	return _group_count_report(spec, filters)


def _group_count_report(spec: dict, filters):
	table = spec["table"]
	group = spec["group"]
	conditions = []
	if frappe.get_meta(table).has_field("company"):
		conditions, filters = branch_conditions(filters)
	if not spec.get("no_date") and spec.get("date"):
		conditions.extend(date_conditions(filters, spec["date"]))
	if spec.get("extra"):
		conditions.append(spec["extra"])
	where = " AND ".join(conditions) if conditions else "1=1"
	data = frappe.db.sql(
		f"""
		SELECT `{group}` AS dimension, COUNT(*) AS record_count
		FROM `tab{table}`
		WHERE {where}
		GROUP BY `{group}`
		ORDER BY record_count DESC
		""",
		filters,
		as_dict=True,
	)
	columns = [
		{"label": _(group.replace("_", " ").title()), "fieldname": "dimension", "fieldtype": "Data", "width": 200},
		{"label": _("Count"), "fieldname": "record_count", "fieldtype": "Int", "width": 100},
	]
	return columns, data


def _lead_time_report(filters):
	conditions, filters = branch_conditions(filters)
	conditions.extend(date_conditions(filters, "appointment_date"))
	data = frappe.db.sql(
		f"""
		SELECT practitioner, specialty, branch,
			AVG(TIMESTAMPDIFF(HOUR, creation, appointment_date)) AS avg_lead_hours,
			COUNT(*) AS appointments
		FROM `tabHealthcare Appointment`
		WHERE {' AND '.join(conditions)}
		GROUP BY practitioner, specialty, branch
		ORDER BY avg_lead_hours DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.avg_lead_hours = flt(row.avg_lead_hours, 2)
	return [
		{"label": _("Practitioner"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 160},
		{"label": _("Specialty"), "fieldname": "specialty", "fieldtype": "Link", "options": "Healthcare Specialty", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": _("Avg Lead (hrs)"), "fieldname": "avg_lead_hours", "fieldtype": "Float", "width": 120},
		{"label": _("Appointments"), "fieldname": "appointments", "fieldtype": "Int", "width": 100},
	], data


def _lab_tat_report(filters):
	conditions, filters = branch_conditions(filters)
	conditions.extend(date_conditions(filters, "collected_datetime"))
	conditions.append("status = 'completed'")
	data = frappe.db.sql(
		f"""
		SELECT branch, sample_type,
			AVG(TIMESTAMPDIFF(HOUR, collected_datetime, modified)) AS avg_tat_hours,
			COUNT(*) AS samples
		FROM `tabHealthcare Lab Sample`
		WHERE {' AND '.join(conditions)}
		GROUP BY branch, sample_type
		ORDER BY avg_tat_hours DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.avg_tat_hours = flt(row.avg_tat_hours, 2)
	return [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Sample Type"), "fieldname": "sample_type", "fieldtype": "Data", "width": 120},
		{"label": _("Avg TAT (hrs)"), "fieldname": "avg_tat_hours", "fieldtype": "Float", "width": 120},
		{"label": _("Samples"), "fieldname": "samples", "fieldtype": "Int", "width": 90},
	], data


def _abnormal_lab_report(filters):
	conditions, filters = branch_conditions(filters)
	conditions.extend(date_conditions(filters, "effective_datetime"))
	conditions.append("abnormal_flag = 1")
	if not frappe.db.has_column("Healthcare Diagnostic Report", "abnormal_flag"):
		return [{"label": _("Note"), "fieldname": "note", "fieldtype": "Data", "width": 300}], [
			{"note": _("No abnormal flags recorded in period.")}
		]
	data = frappe.db.sql(
		f"""
		SELECT patient, branch, report_category AS category, COUNT(*) AS abnormal_reports
		FROM `tabHealthcare Diagnostic Report`
		WHERE {' AND '.join(conditions)}
		GROUP BY patient, branch, report_category
		ORDER BY abnormal_reports DESC
		LIMIT 200
		""",
		filters,
		as_dict=True,
	)
	return [
		{"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Healthcare Patient", "width": 160},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 120},
		{"label": _("Abnormal Reports"), "fieldname": "abnormal_reports", "fieldtype": "Int", "width": 120},
	], data


def _rad_tat_report(filters):
	conditions, filters = branch_conditions(filters)
	conditions.extend(date_conditions(filters, "authored_on"))
	conditions.append("request_category = 'imaging'")
	conditions.append("status = 'completed'")
	data = frappe.db.sql(
		f"""
		SELECT branch, modality,
			AVG(TIMESTAMPDIFF(HOUR, authored_on, modified)) AS avg_tat_hours,
			COUNT(*) AS studies
		FROM `tabHealthcare Service Request`
		WHERE {' AND '.join(conditions)}
		GROUP BY branch, modality
		ORDER BY avg_tat_hours DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.avg_tat_hours = flt(row.avg_tat_hours, 2)
	return [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Modality"), "fieldname": "modality", "fieldtype": "Data", "width": 120},
		{"label": _("Avg TAT (hrs)"), "fieldname": "avg_tat_hours", "fieldtype": "Float", "width": 120},
		{"label": _("Studies"), "fieldname": "studies", "fieldtype": "Int", "width": 90},
	], data


def _below_par_report(filters):
	if not frappe.db.exists("DocType", "Healthcare Item Par Level"):
		return [{"label": _("Note"), "fieldname": "note", "fieldtype": "Data", "width": 300}], []
	filters = require_company(filters)
	conditions = ["p.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("p.branch = %(branch)s")
	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return [{"label": _("Note"), "fieldname": "note", "fieldtype": "Data", "width": 300}], []
		filters.allowed_branches = tuple(allowed)
		conditions.append("p.branch in %(allowed_branches)s")
	data = frappe.db.sql(
		f"""
		SELECT p.item, p.warehouse, p.par_level, i.current_stock_qty AS on_hand,
			(p.par_level - IFNULL(i.current_stock_qty, 0)) AS shortage
		FROM `tabHealthcare Item Par Level` p
		LEFT JOIN `tabItem` i ON i.name = p.item
		WHERE {' AND '.join(conditions)} AND IFNULL(i.current_stock_qty, 0) < p.par_level
		ORDER BY shortage DESC
		""",
		filters,
		as_dict=True,
	)
	return [
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 160},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": _("Par Level"), "fieldname": "par_level", "fieldtype": "Float", "width": 100},
		{"label": _("On Hand"), "fieldname": "on_hand", "fieldtype": "Float", "width": 100},
		{"label": _("Shortage"), "fieldname": "shortage", "fieldtype": "Float", "width": 100},
	], data
