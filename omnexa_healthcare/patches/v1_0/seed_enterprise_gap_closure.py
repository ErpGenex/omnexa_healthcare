# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.specialty_engine import seed_default_specialty_modules


def execute():
	created = seed_default_specialty_modules()
	settings = frappe.get_doc("Healthcare Settings")
	settings.enforce_mfa_for_phi_roles = 1
	settings.enable_sms_reminders = 1
	settings.enable_whatsapp_reminders = 1
	settings.enable_ai_scheduling = 1
	settings.enable_llm_clinical_documentation = 1
	settings.save(ignore_permissions=True)
	if not frappe.db.exists("Healthcare Treatment Package", "DENTAL-CHECKUP"):
		pkg = frappe.get_doc(
			{
				"doctype": "Healthcare Treatment Package",
				"package_code": "DENTAL-CHECKUP",
				"package_name": "Dental Checkup Package",
				"total_price": 500,
				"is_active": 1,
				"items": [{"procedure": "Exam + Cleaning", "qty": 1, "rate": 500}],
			}
		)
		pkg.insert(ignore_permissions=True)
	frappe.logger("omnexa_healthcare").info(f"seed_enterprise_gap_closure: specialties+{created}, settings enabled")
