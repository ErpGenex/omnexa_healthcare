# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe

from omnexa_core.omnexa_core.branch_access import enforce_branch_access, get_allowed_branches
from omnexa_core.omnexa_core.user_context import apply_company_branch_defaults


def enforce_branch_access_for_doc(doc, method=None):
	enforce_branch_access(doc)


def populate_company_branch_from_user_context(doc, method=None):
	apply_company_branch_defaults(doc)


def _get_query_for_table(table: str, user=None):
	user = user or frappe.session.user
	allowed = get_allowed_branches(user)
	if allowed is None:
		return ""
	if not allowed:
		return "1=0"
	quoted = ", ".join([frappe.db.escape(v) for v in allowed])
	return f"(`tab{table}`.branch in ({quoted}) or `tab{table}`.branch is null or `tab{table}`.branch = '')"


def healthcare_patient_query_conditions(user=None):
	return _get_query_for_table("Healthcare Patient", user)


def healthcare_appointment_query_conditions(user=None):
	return _get_query_for_table("Healthcare Appointment", user)


def healthcare_facility_profile_query_conditions(user=None):
	return _get_query_for_table("Healthcare Facility Profile", user)


def healthcare_department_query_conditions(user=None):
	return _get_query_for_table("Healthcare Department", user)


def healthcare_service_unit_query_conditions(user=None):
	return _get_query_for_table("Healthcare Service Unit", user)


def healthcare_encounter_query_conditions(user=None):
	return _get_query_for_table("Healthcare Encounter", user)


def healthcare_episode_of_care_query_conditions(user=None):
	return _get_query_for_table("Healthcare Episode Of Care", user)


def healthcare_clinical_condition_query_conditions(user=None):
	return _get_query_for_table("Healthcare Clinical Condition", user)


def healthcare_allergy_intolerance_query_conditions(user=None):
	return _get_query_for_table("Healthcare Allergy Intolerance", user)


def healthcare_medication_statement_query_conditions(user=None):
	return _get_query_for_table("Healthcare Medication Statement", user)


def healthcare_immunization_query_conditions(user=None):
	return _get_query_for_table("Healthcare Immunization", user)


def healthcare_observation_query_conditions(user=None):
	return _get_query_for_table("Healthcare Observation", user)


def healthcare_service_request_query_conditions(user=None):
	return _get_query_for_table("Healthcare Service Request", user)


def healthcare_diagnostic_report_query_conditions(user=None):
	return _get_query_for_table("Healthcare Diagnostic Report", user)


def healthcare_bed_query_conditions(user=None):
	return _get_query_for_table("Healthcare Bed", user)


def healthcare_admission_query_conditions(user=None):
	return _get_query_for_table("Healthcare Admission", user)


def healthcare_service_charge_query_conditions(user=None):
	return _get_query_for_table("Healthcare Service Charge", user)


def healthcare_medication_dispense_query_conditions(user=None):
	return _get_query_for_table("Healthcare Medication Dispense", user)


def healthcare_lab_sample_query_conditions(user=None):
	return _get_query_for_table("Healthcare Lab Sample", user)


def healthcare_practitioner_query_conditions(user=None):
	# Practitioners are company-scoped; branch assignments are in child table.
	return ""


def healthcare_procedure_order_query_conditions(user=None):
	return _get_query_for_table("Healthcare Procedure Order", user)


def healthcare_patient_coverage_query_conditions(user=None):
	return _get_query_for_table("Healthcare Patient Coverage", user)


def healthcare_insurance_claim_query_conditions(user=None):
	return _get_query_for_table("Healthcare Insurance Claim", user)


def healthcare_operating_room_query_conditions(user=None):
	return _get_query_for_table("Healthcare Operating Room", user)


def healthcare_surgical_case_query_conditions(user=None):
	return _get_query_for_table("Healthcare Surgical Case", user)


def healthcare_companion_stay_query_conditions(user=None):
	return _get_query_for_table("Healthcare Companion Stay", user)


def healthcare_critical_care_monitoring_query_conditions(user=None):
	return _get_query_for_table("Healthcare Critical Care Monitoring", user)
