# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, get_time, today


class HealthcareDiagnosticReport(Document):
	def get_lab_print_context(self) -> dict:
		"""Context for Omnexa Lab Report print format."""
		patient_doc = frappe.get_doc("Healthcare Patient", self.patient) if self.patient else None
		branch_doc = frappe.get_doc("Branch", self.branch) if self.branch else None
		company_doc = frappe.get_doc("Company", self.company) if self.company else None

		patient_id = ""
		if patient_doc:
			patient_id = (
				frappe.db.get_value(
					"Healthcare Patient Identifier",
					{"parent": patient_doc.name, "parenttype": "Healthcare Patient"},
					"value",
					order_by="creation asc",
				)
				or patient_doc.name
			)

		age_years = ""
		if patient_doc and patient_doc.birth_date:
			age_years = str(date_diff(getdate(today()), getdate(patient_doc.birth_date)) // 365)

		gender = (patient_doc.gender or "unknown").title() if patient_doc else ""
		gender_ar = {"Male": "ذكر", "Female": "أنثى"}.get(gender, gender)

		effective = self.effective_datetime
		report_date = ""
		report_time = ""
		if effective:
			report_date = frappe.format(effective, {"fieldtype": "Date"})
			report_time = frappe.format(get_time(str(effective)), {"fieldtype": "Time"})

		lab_settings = frappe.get_single("Healthcare Settings") if frappe.db.exists("DocType", "Healthcare Settings") else None
		lab_name_en = (getattr(lab_settings, "lab_report_title_en", None) if lab_settings else None) or (
			company_doc.company_name if company_doc else "Medical Laboratory"
		)
		lab_name_ar = (getattr(lab_settings, "lab_report_title_ar", None) if lab_settings else None) or "مختبر طبي"
		lab_slogan_ar = (getattr(lab_settings, "lab_report_slogan_ar", None) if lab_settings else None) or "دقة النتائج .. سرنا"
		lab_phone = (getattr(lab_settings, "lab_report_phone", None) if lab_settings else None) or ""
		lab_address = (getattr(lab_settings, "lab_report_address", None) if lab_settings else None) or (
			(getattr(branch_doc, "branch_name", None) or getattr(branch_doc, "name", "")) if branch_doc else ""
		)

		return {
			"lab_name_en": lab_name_en,
			"lab_name_ar": lab_name_ar,
			"lab_slogan_ar": lab_slogan_ar,
			"lab_phone": lab_phone,
			"lab_address": lab_address,
			"patient_name": self.patient_display or (patient_doc.full_name if patient_doc else ""),
			"patient_id": patient_id,
			"patient_age": age_years,
			"patient_gender": gender,
			"patient_gender_ar": gender_ar,
			"lab_no": self.name,
			"report_date": report_date,
			"report_time": report_time,
			"grouped_results": self.get_lab_results_grouped(),
		}

	def get_lab_results_grouped(self) -> list[dict]:
		"""Return lab result rows grouped by section for printing."""
		groups: list[dict] = []
		current: dict | None = None
		for row in self.lab_results or []:
			if row.is_section_header:
				current = {"section": row.section or row.test_name, "tests": []}
				groups.append(current)
				continue
			section = row.section or (current["section"] if current else _("General"))
			if not current or current.get("section") != section:
				current = {"section": section, "tests": []}
				groups.append(current)
			current["tests"].append(
				{
					"test_name": row.test_name,
					"result_value": row.result_value,
					"unit": row.unit,
					"reference_range": row.reference_range,
					"is_abnormal": row.is_abnormal,
				}
			)
		return groups
