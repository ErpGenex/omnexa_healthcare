# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Multi-visit specialty follow-up plans — orthopedics, antenatal, oncology, etc."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today

from omnexa_healthcare.follow_up_templates import FOLLOW_UP_PLAN_TEMPLATES, MULTI_VISIT_MODULE_CODES


def _json_load(val):
	if not val:
		return {}
	if isinstance(val, dict):
		return val
	try:
		return json.loads(val)
	except Exception:
		return {}


def _resolve_module_code(specialty: str) -> str | None:
	if not specialty:
		return None
	if specialty in FOLLOW_UP_PLAN_TEMPLATES:
		return specialty
	mod_code = frappe.db.get_value("Healthcare Specialty Module", {"specialty": specialty, "is_active": 1}, "module_code")
	if mod_code:
		return mod_code
	spec_name = frappe.db.get_value("Healthcare Specialty", specialty, "specialty_name")
	if not spec_name:
		return None
	for code, cfg in FOLLOW_UP_PLAN_TEMPLATES.items():
		if cfg.get("supports_multi_visit"):
			row_name = frappe.db.get_value("Healthcare Specialty Module", code, "specialty")
			row_label = frappe.db.get_value("Healthcare Specialty", row_name, "specialty_name") if row_name else None
			if row_label and row_label.lower() == (spec_name or "").lower():
				return code
	return None


def _get_template_config(module_code: str) -> dict:
	row = frappe.db.get_value("Healthcare Specialty Module", module_code, "follow_up_workflow", as_dict=False)
	parsed = _json_load(row)
	if parsed.get("templates"):
		return parsed
	return FOLLOW_UP_PLAN_TEMPLATES.get(module_code, {})


@frappe.whitelist()
def list_multi_visit_specialties() -> list[dict]:
	rows = []
	for module_code in sorted(MULTI_VISIT_MODULE_CODES):
		cfg = _get_template_config(module_code)
		mod = frappe.db.get_value(
			"Healthcare Specialty Module",
			module_code,
			["module_name", "specialty"],
			as_dict=True,
		)
		if not mod:
			continue
		rows.append(
			{
				"module_code": module_code,
				"module_name": mod.module_name,
				"specialty": mod.specialty,
				"specialty_name": frappe.db.get_value("Healthcare Specialty", mod.specialty, "specialty_name"),
				"plan_types": cfg.get("plan_types", []),
				"default_plan_type": cfg.get("default_plan_type"),
				"visit_count": len((cfg.get("templates") or {}).get(cfg.get("default_plan_type", ""), {}).get("visits", [])),
			}
		)
	return rows


@frappe.whitelist()
def get_follow_up_templates(specialty: str, plan_type: str | None = None) -> dict:
	module_code = _resolve_module_code(specialty)
	if not module_code or module_code not in MULTI_VISIT_MODULE_CODES:
		frappe.throw(_("Specialty {0} does not support multi-visit follow-up plans.").format(specialty))
	cfg = _get_template_config(module_code)
	pt = plan_type or cfg.get("default_plan_type") or "general"
	tpl = (cfg.get("templates") or {}).get(pt)
	if not tpl:
		frappe.throw(_("No follow-up template for plan type {0}").format(pt))
	return {
		"module_code": module_code,
		"plan_type": pt,
		"plan_title": tpl.get("plan_title"),
		"visits": tpl.get("visits", []),
		"plan_types": cfg.get("plan_types", []),
	}


@frappe.whitelist()
def create_follow_up_plan(
	patient: str,
	specialty: str,
	plan_type: str | None = None,
	plan_title: str | None = None,
	practitioner: str | None = None,
	encounter: str | None = None,
	company: str | None = None,
	branch: str | None = None,
	start_date: str | None = None,
) -> dict:
	if not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient does not exist."), title=_("Patient"))
	tpl_data = get_follow_up_templates(specialty, plan_type)
	pt = tpl_data["plan_type"]
	base = getdate(start_date or today())
	patient_row = frappe.db.get_value("Healthcare Patient", patient, ["company", "branch"], as_dict=True)
	company = company or patient_row.company
	branch = branch or patient_row.branch
	specialty_link = specialty
	if not frappe.db.exists("Healthcare Specialty", specialty):
		specialty_link = frappe.db.get_value("Healthcare Specialty Module", tpl_data["module_code"], "specialty") or specialty

	visits = []
	for idx, row in enumerate(tpl_data.get("visits") or [], start=1):
		visits.append(
			{
				"visit_no": idx,
				"planned_date": add_days(base, int(row.get("offset_days") or 0)),
				"visit_objective": row.get("visit_objective") or row.get("procedure") or f"Visit {idx}",
				"procedure": row.get("procedure"),
				"status": "planned",
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Follow Up Plan",
			"patient": patient,
			"plan_title": plan_title or tpl_data.get("plan_title"),
			"plan_type": pt,
			"specialty": specialty_link,
			"practitioner": practitioner,
			"encounter": encounter,
			"company": company,
			"branch": branch,
			"status": "active",
			"start_date": base,
			"expected_end_date": visits[-1]["planned_date"] if visits else base,
			"visits": visits,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "plan_title": doc.plan_title, "visit_count": len(visits)}


@frappe.whitelist()
def get_patient_follow_up_plans(patient: str, specialty: str | None = None) -> list[dict]:
	filters: dict = {"patient": patient, "docstatus": ["<", 2]}
	if specialty:
		filters["specialty"] = specialty
	rows = frappe.get_all(
		"Healthcare Follow Up Plan",
		filters=filters,
		fields=["name", "plan_title", "plan_type", "specialty", "status", "start_date", "expected_end_date"],
		order_by="modified desc",
	)
	for row in rows:
		row["specialty_name"] = frappe.db.get_value("Healthcare Specialty", row.specialty, "specialty_name")
		row["visits_total"] = frappe.db.count("Healthcare Follow Up Plan Visit", {"parent": row.name})
		row["visits_completed"] = frappe.db.count(
			"Healthcare Follow Up Plan Visit", {"parent": row.name, "status": "completed"}
		)
		row["progress_pct"] = round(row["visits_completed"] / row["visits_total"] * 100) if row["visits_total"] else 0
	return rows


@frappe.whitelist()
def get_follow_up_plan_detail(plan: str) -> dict:
	doc = frappe.get_doc("Healthcare Follow Up Plan", plan)
	return {
		"name": doc.name,
		"patient": doc.patient,
		"plan_title": doc.plan_title,
		"plan_type": doc.plan_type,
		"specialty": doc.specialty,
		"status": doc.status,
		"start_date": doc.start_date,
		"expected_end_date": doc.expected_end_date,
		"visits": [
			{
				"visit_no": v.visit_no,
				"planned_date": v.planned_date,
				"visit_objective": v.visit_objective,
				"procedure": v.procedure,
				"status": v.status,
				"appointment": v.appointment,
				"encounter": v.encounter,
			}
			for v in doc.visits
		],
	}
