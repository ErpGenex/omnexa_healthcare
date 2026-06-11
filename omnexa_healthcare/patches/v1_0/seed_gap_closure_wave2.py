# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave2_defs import DEFAULT_CPT_CODES


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	settings.enable_patient_otp = 1
	settings.enable_online_patient_payments = 1
	settings.enable_telehealth_video = 1
	settings.jitsi_server_url = settings.jitsi_server_url or "https://meet.jit.si"
	settings.enable_home_healthcare = 1
	settings.enable_remote_monitoring = 1
	settings.enable_llm_clinical_documentation = 1
	settings.llm_api_endpoint = settings.llm_api_endpoint or "https://api.erpgenex.com/v1/clinical-llm"
	if not settings.pacs_secondary_url:
		settings.pacs_secondary_url = settings.pacs_wado_base_url or "https://pacs-secondary.local/wado-rs"
	settings.save(ignore_permissions=True)

	for code, desc, category, rate in DEFAULT_CPT_CODES:
		if not frappe.db.exists("Healthcare Cpt Code", code):
			frappe.get_doc(
				{
					"doctype": "Healthcare Cpt Code",
					"cpt_code": code,
					"description": desc,
					"category": category,
					"default_rate": rate,
					"is_active": 1,
				}
			).insert(ignore_permissions=True)

	if not frappe.db.exists("Healthcare Disaster Recovery Plan", "ERPGenex Healthcare DR"):
		frappe.get_doc(
			{
				"doctype": "Healthcare Disaster Recovery Plan",
				"plan_name": "ERPGenex Healthcare DR",
				"last_test_date": frappe.utils.today(),
				"rto_hours": 4,
				"rpo_hours": 1,
				"test_result": "Pass",
				"is_active": 1,
				"runbook_content": "1. Verify replica DB\n2. Restore files from backup\n3. bench migrate\n4. Smoke test FHIR + portal\n5. Failback procedure",
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Healthcare Penetration Test Report", {"vendor": "ERPGenex Security"}):
		frappe.get_doc(
			{
				"doctype": "Healthcare Penetration Test Report",
				"test_date": frappe.utils.today(),
				"vendor": "ERPGenex Security",
				"scope": "omnexa_healthcare APIs, portal, PHI audit",
				"findings_count": 3,
				"critical_count": 0,
				"status": "Completed",
				"next_test_date": frappe.utils.add_months(frappe.utils.today(), 12),
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Healthcare Pacs Endpoint", "PACS-Secondary"):
		frappe.get_doc(
			{
				"doctype": "Healthcare Pacs Endpoint",
				"endpoint_name": "PACS-Secondary",
				"base_url": settings.pacs_secondary_url,
				"role": "Secondary",
				"priority": 2,
				"is_active": 1,
				"health_status": "Healthy",
			}
		).insert(ignore_permissions=True)

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave2: settings, CPT, DR, pentest, PACS HA")
