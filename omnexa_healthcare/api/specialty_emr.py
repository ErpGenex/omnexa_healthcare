# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Specialty EMR — clinical templates and structured forms."""

from __future__ import annotations

import frappe
from frappe import _


SPECIALTY_FORMS: dict[str, dict] = {
	"General Medicine": {"sections": ["SOAP", "Vitals", "Plan"]},
	"Pediatrics": {"sections": ["Growth Chart", "Immunization Review", "SOAP"]},
	"OB/GYN": {"sections": ["Obstetric History", "LMP", "Fundal Height", "Plan"]},
	"Dermatology": {"sections": ["Lesion Description", "Distribution", "Biopsy Plan"]},
	"ENT": {"sections": ["Ear Exam", "Nose Exam", "Throat Exam"]},
	"Ophthalmology": {"sections": ["Visual Acuity", "IOP", "Fundoscopy"]},
	"Dental": {"sections": ["Tooth Chart", "Periodontal", "Treatment Plan"]},
	"Orthopedics": {"sections": ["Joint Exam", "ROM", "Imaging Review"]},
	"Cardiology": {"sections": ["Cardiac History", "ECG", "Echo Summary"]},
	"Psychiatry": {"sections": ["MSE", "Risk Assessment", "Plan"]},
}


@frappe.whitelist()
def apply_clinical_template(encounter: str, template: str | None = None, specialty: str | None = None) -> dict:
	enc = frappe.get_doc("Healthcare Encounter", encounter)
	spec = specialty or enc.specialty
	if template:
		tpl = frappe.get_doc("Healthcare Clinical Template", template)
	elif spec:
		tpl_name = frappe.db.get_value("Healthcare Clinical Template", {"specialty": spec, "is_active": 1}, "name")
		if not tpl_name:
			frappe.throw(_("No active clinical template for specialty {0}").format(spec))
		tpl = frappe.get_doc("Healthcare Clinical Template", tpl_name)
	else:
		frappe.throw(_("template or specialty is required"))

	structured = {
		"chief_complaint_hint": tpl.chief_complaint_hint,
		"assessment": tpl.assessment_template,
		"plan": tpl.plan_template,
		"specialty_form": _specialty_form(spec),
	}
	enc.db_set("clinical_template", tpl.name)
	enc.db_set("structured_clinical_data", frappe.as_json(structured))
	if tpl.chief_complaint_hint and not enc.chief_complaint:
		enc.db_set("chief_complaint", tpl.chief_complaint_hint)
	return {"encounter": enc.name, "template": tpl.name, "structured": structured}


@frappe.whitelist()
def list_specialty_forms() -> dict:
	return SPECIALTY_FORMS


def validate_icd10_code(code: str | None) -> None:
	if not code:
		return
	if not frappe.db.exists("Healthcare Icd10 Code", {"code": code, "is_active": 1}):
		frappe.throw(_("ICD-10 code {0} is not in master or inactive.").format(code), title=_("ICD-10"))


def validate_icd11_code(code: str | None) -> None:
	if not code:
		return
	if not frappe.db.exists("Healthcare Icd11 Code", {"code": code, "is_active": 1}):
		frappe.throw(_("ICD-11 code {0} is not in master or inactive.").format(code), title=_("ICD-11"))


def _specialty_form(specialty: str | None) -> dict:
	if not specialty:
		return {}
	try:
		from omnexa_healthcare.specialty_engine import get_specialty_module_for_specialty

		mod = get_specialty_module_for_specialty(specialty)
		if mod and mod.get("encounter_sections"):
			return {"sections": mod["encounter_sections"], "module_code": mod.get("module_code"), "chart_type": mod.get("chart_type")}
	except Exception:
		pass
	spec_name = frappe.db.get_value("Healthcare Specialty", specialty, "specialty_name") or specialty
	for key, form in SPECIALTY_FORMS.items():
		if key.lower() in (spec_name or "").lower():
			return form
	return {"sections": ["SOAP"]}
