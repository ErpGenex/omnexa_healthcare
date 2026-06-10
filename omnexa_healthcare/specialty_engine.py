# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Dynamic Specialty Engine — config-driven workflows without per-specialty code."""

from __future__ import annotations

import json

import frappe
from frappe import _


DEFAULT_SPECIALTY_MODULES: list[dict] = [
	{
		"module_code": "general_medicine",
		"module_name": "General Medicine",
		"specialty_name": "General Medicine",
		"chart_type": "none",
		"encounter_sections": ["SOAP", "Vitals", "Plan"],
	},
	{
		"module_code": "dental",
		"module_name": "Dental Center of Excellence",
		"specialty_name": "Dental",
		"chart_type": "dental_fdi",
		"encounter_sections": ["Tooth Chart", "Periodontal", "Treatment Plan", "Imaging"],
		"consultation_workflow": {"steps": ["intake", "charting", "treatment_plan", "consent", "billing"]},
		"billing_workflow": {"supports": ["cash", "insurance", "installment", "package"]},
	},
	{
		"module_code": "cardiology",
		"module_name": "Cardiology",
		"specialty_name": "Cardiology",
		"chart_type": "custom",
		"encounter_sections": ["Cardiac History", "ECG", "Echo Summary", "Plan"],
	},
	{
		"module_code": "pediatrics",
		"module_name": "Pediatrics",
		"specialty_name": "Pediatrics",
		"chart_type": "none",
		"encounter_sections": ["Growth Chart", "Immunization Review", "SOAP"],
	},
	{"module_code": "dermatology", "module_name": "Dermatology", "specialty_name": "Dermatology", "chart_type": "body_map", "encounter_sections": ["Lesion Description", "Distribution", "Biopsy Plan"]},
	{"module_code": "ophthalmology", "module_name": "Ophthalmology", "specialty_name": "Ophthalmology", "chart_type": "custom", "encounter_sections": ["Visual Acuity", "IOP", "Fundoscopy"]},
	{"module_code": "orthopedics", "module_name": "Orthopedics", "specialty_name": "Orthopedics", "chart_type": "body_map", "encounter_sections": ["Joint Exam", "ROM", "Imaging Review"]},
	{"module_code": "ent", "module_name": "ENT", "specialty_name": "ENT", "chart_type": "none", "encounter_sections": ["Ear Exam", "Nose Exam", "Throat Exam"]},
	{"module_code": "gynecology", "module_name": "Gynecology", "specialty_name": "Gynecology", "chart_type": "none", "encounter_sections": ["Obstetric History", "LMP", "Exam", "Plan"]},
	{"module_code": "surgery", "module_name": "Surgery", "specialty_name": "Surgery", "chart_type": "none", "encounter_sections": ["Pre-Op", "Procedure", "Post-Op"]},
	{"module_code": "psychiatry", "module_name": "Psychiatry", "specialty_name": "Psychiatry", "chart_type": "none", "encounter_sections": ["MSE", "Risk Assessment", "Plan"]},
	{"module_code": "physiotherapy", "module_name": "Physiotherapy", "specialty_name": "Physiotherapy", "chart_type": "body_map", "encounter_sections": ["Assessment", "Treatment", "Home Program"]},
	{"module_code": "oncology", "module_name": "Oncology", "specialty_name": "Oncology", "chart_type": "none", "encounter_sections": ["Staging", "Chemo Plan", "Supportive Care"]},
	{"module_code": "neurology", "module_name": "Neurology", "specialty_name": "Neurology", "chart_type": "none", "encounter_sections": ["Neuro Exam", "Imaging", "Plan"]},
	{"module_code": "urology", "module_name": "Urology", "specialty_name": "Urology", "chart_type": "none", "encounter_sections": ["History", "Exam", "Plan"]},
	{"module_code": "gastroenterology", "module_name": "Gastroenterology", "specialty_name": "Gastroenterology", "chart_type": "none", "encounter_sections": ["GI History", "Exam", "Endoscopy Plan"]},
]


def _json_load(val):
	if not val:
		return {}
	if isinstance(val, dict):
		return val
	try:
		return json.loads(val)
	except Exception:
		return {}


def get_specialty_module_for_specialty(specialty: str | None) -> dict | None:
	if not specialty:
		return None
	row = frappe.db.get_value(
		"Healthcare Specialty Module",
		{"specialty": specialty, "is_active": 1},
		["name", "module_code", "module_name", "chart_type", "encounter_sections", "consultation_workflow", "procedure_workflow", "billing_workflow", "insurance_workflow", "inventory_workflow"],
		as_dict=True,
	)
	if not row:
		return None
	return {
		"name": row.name,
		"module_code": row.module_code,
		"module_name": row.module_name,
		"chart_type": row.chart_type,
		"encounter_sections": _json_load(row.encounter_sections) or [],
		"consultation_workflow": _json_load(row.consultation_workflow),
		"procedure_workflow": _json_load(row.procedure_workflow),
		"billing_workflow": _json_load(row.billing_workflow),
		"insurance_workflow": _json_load(row.insurance_workflow),
		"inventory_workflow": _json_load(row.inventory_workflow),
	}


@frappe.whitelist()
def list_specialty_modules() -> list[dict]:
	rows = frappe.get_all(
		"Healthcare Specialty Module",
		filters={"is_active": 1},
		fields=["name", "module_code", "module_name", "specialty", "chart_type"],
		order_by="module_name",
	)
	return rows


@frappe.whitelist()
def get_specialty_module_config(specialty: str) -> dict:
	mod = get_specialty_module_for_specialty(specialty)
	if mod:
		return mod
	frappe.throw(_("No active specialty module for {0}").format(specialty), title=_("Specialty Module"))


@frappe.whitelist()
def seed_default_specialty_modules(company: str | None = None) -> int:
	created = 0
	for spec in DEFAULT_SPECIALTY_MODULES:
		specialty_name = spec["specialty_name"]
		specialty = frappe.db.get_value("Healthcare Specialty", {"specialty_name": specialty_name})
		if not specialty:
			doc = frappe.get_doc(
				{
					"doctype": "Healthcare Specialty",
					"specialty_code": spec["module_code"].upper()[:12],
					"specialty_name": specialty_name,
					"is_active": 1,
					**({"company": company} if company else {}),
				}
			)
			doc.insert(ignore_permissions=True)
			specialty = doc.name
		if frappe.db.exists("Healthcare Specialty Module", spec["module_code"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Specialty Module",
				"module_code": spec["module_code"],
				"module_name": spec["module_name"],
				"specialty": specialty,
				"chart_type": spec.get("chart_type", "none"),
				"encounter_sections": json.dumps(spec.get("encounter_sections", [])),
				"consultation_workflow": json.dumps(spec.get("consultation_workflow", {})),
				"billing_workflow": json.dumps(spec.get("billing_workflow", {})),
				"is_active": 1,
				**({"company": company} if company else {}),
			}
		)
		doc.insert(ignore_permissions=True)
		created += 1
	return created
