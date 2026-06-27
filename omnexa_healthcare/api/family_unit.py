# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Family Medicine — household units, members, dashboard, dependent migration."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import today


def _existing_fields(doctype: str, *fields: str) -> list[str]:
	meta = frappe.get_meta(doctype)
	return [field for field in fields if meta.has_field(field)]


@frappe.whitelist()
def list_family_units(company: str | None = None, branch: str | None = None, limit: int = 50) -> list[dict]:
	limit = min(int(limit or 50), 200)
	filters: dict = {"household_status": "Active"}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	return frappe.get_all(
		"Healthcare Family Unit",
		filters=filters,
		fields=[
			"name",
			"family_number",
			"family_name",
			"head_of_family",
			"primary_care_practitioner",
			"household_status",
			"branch",
			"company",
		],
		limit=limit,
		order_by="modified desc",
	)


@frappe.whitelist()
def get_family_unit(family_unit: str) -> dict:
	doc = frappe.get_doc("Healthcare Family Unit", family_unit)
	return doc.as_dict()


@frappe.whitelist()
def create_family_unit(
	family_number: str,
	family_name: str,
	head_of_family: str,
	company: str,
	branch: str,
	members: str | list | None = None,
	primary_care_practitioner: str | None = None,
	shared_genetic_risk_notes: str | None = None,
) -> dict:
	if isinstance(members, str):
		members = json.loads(members) if members else []
	members = members or []
	if not any(m.get("patient") == head_of_family for m in members):
		members.insert(
			0,
			{
				"patient": head_of_family,
				"relationship": "Head",
				"is_primary_contact": 1,
			},
		)
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Family Unit",
			"family_number": family_number,
			"family_name": family_name,
			"head_of_family": head_of_family,
			"primary_care_practitioner": primary_care_practitioner,
			"shared_genetic_risk_notes": shared_genetic_risk_notes,
			"household_status": "Active",
			"company": company,
			"branch": branch,
			"members": members,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "name": doc.name, "family_number": doc.family_number}


@frappe.whitelist()
def link_patient_to_family(
	family_unit: str,
	patient: str,
	relationship: str,
	is_primary_contact: int = 0,
) -> dict:
	doc = frappe.get_doc("Healthcare Family Unit", family_unit)
	for row in doc.members or []:
		if row.patient == patient:
			row.relationship = relationship
			if is_primary_contact:
				for m in doc.members:
					m.is_primary_contact = 1 if m.patient == patient else 0
			doc.save(ignore_permissions=True)
			return {"ok": True, "updated": True, "name": doc.name}
	doc.append(
		"members",
		{
			"patient": patient,
			"relationship": relationship,
			"is_primary_contact": is_primary_contact,
			"enrollment_date": today(),
		},
	)
	if is_primary_contact:
		for m in doc.members:
			m.is_primary_contact = 1 if m.patient == patient else 0
	doc.save(ignore_permissions=True)
	return {"ok": True, "updated": False, "name": doc.name}


@frappe.whitelist()
def get_family_dashboard(family_unit: str) -> dict:
	unit = frappe.get_doc("Healthcare Family Unit", family_unit)
	member_ids = [m.patient for m in unit.members or [] if m.patient]
	members_detail: list[dict] = []
	for mid in member_ids:
		meta = frappe.get_meta("Healthcare Patient")
		name_field = "full_name" if meta.has_field("full_name") else "patient_name"
		dob_field = "birth_date" if meta.has_field("birth_date") else "date_of_birth"
		fields = ["name", name_field, "gender", dob_field]
		if meta.has_field("status"):
			fields.append("status")
		patient = frappe.db.get_value("Healthcare Patient", mid, fields, as_dict=True)
		if not patient:
			continue
		if name_field != "patient_name" and name_field in patient:
			patient["patient_name"] = patient.get(name_field)
		if dob_field != "date_of_birth" and dob_field in patient:
			patient["date_of_birth"] = patient.get(dob_field)
		row = next((m for m in unit.members if m.patient == mid), None)
		members_detail.append(
			{
				**patient,
				"relationship": row.relationship if row else "",
				"is_primary_contact": row.is_primary_contact if row else 0,
			}
		)

	open_encounters = []
	chronic_conditions = []
	immunizations = []
	follow_ups = []
	if member_ids:
		enc_meta = frappe.get_meta("Healthcare Encounter")
		date_field = "encounter_date" if enc_meta.has_field("encounter_date") else "period_start"
		enc_fields = ["name", "patient", "status"]
		if enc_meta.has_field(date_field):
			enc_fields.append(date_field)
		if enc_meta.has_field("chief_complaint"):
			enc_fields.append("chief_complaint")
		open_encounters = frappe.get_all(
			"Healthcare Encounter",
			filters={
				"patient": ["in", member_ids],
				"docstatus": 1,
				"status": ["in", ["Open", "In Progress"]],
			},
			fields=enc_fields,
			limit=20,
			order_by=f"{date_field} desc" if enc_meta.has_field(date_field) else "modified desc",
		)
		for row in open_encounters:
			if date_field != "encounter_date" and row.get(date_field):
				row["encounter_date"] = row.get(date_field)
		chronic_fields = _existing_fields(
			"Healthcare Clinical Condition",
			"name",
			"patient",
			"code",
			"icd10_code",
			"description",
			"clinical_status",
		)
		chronic_conditions = frappe.get_all(
			"Healthcare Clinical Condition",
			filters={"patient": ["in", member_ids], "clinical_status": ["in", ["Active", "Recurrence"]]},
			fields=chronic_fields or ["name", "patient"],
			limit=30,
		)
		for row in chronic_conditions:
			if not row.get("code") and row.get("icd10_code"):
				row["code"] = row.get("icd10_code")
		imm_fields = _existing_fields(
			"Healthcare Immunization",
			"name",
			"patient",
			"vaccine_code",
			"occurrence_datetime",
			"status",
		)
		immunizations = frappe.get_all(
			"Healthcare Immunization",
			filters={"patient": ["in", member_ids]},
			fields=imm_fields or ["name", "patient"],
			limit=20,
			order_by="occurrence_datetime desc" if "occurrence_datetime" in imm_fields else "modified desc",
		)
		if frappe.db.exists("DocType", "Healthcare Follow Up Plan"):
			fu_fields = _existing_fields(
				"Healthcare Follow Up Plan",
				"name",
				"patient",
				"plan_title",
				"status",
				"progress_pct",
			)
			follow_ups = frappe.get_all(
				"Healthcare Follow Up Plan",
				filters={"patient": ["in", member_ids], "status": ["in", ["Active", "Draft"]]},
				fields=fu_fields or ["name", "patient"],
				limit=20,
			)

	history = frappe.get_all(
		"Healthcare Family History",
		filters={"family_unit": family_unit},
		fields=[
			"name",
			"condition_category",
			"condition_description",
			"relative_relationship",
			"patient",
			"icd10_code",
			"icd11_code",
		],
		limit=50,
	)

	preventive = frappe.get_all(
		"Healthcare Preventive Care Plan",
		filters={"family_unit": family_unit, "status": ["in", ["Active", "Draft"]]},
		fields=["name", "plan_title", "patient", "status", "start_date"],
		limit=20,
	)

	risk_scores = frappe.get_all(
		"Healthcare Family Risk Score",
		filters={"family_unit": family_unit},
		fields=[
			"name",
			"patient",
			"assessment_date",
			"cardiovascular_risk_score",
			"diabetes_risk_score",
			"overall_risk_level",
		],
		limit=10,
		order_by="assessment_date desc",
	)

	alerts: list[dict] = []
	for rs in risk_scores[:3]:
		if rs.overall_risk_level in ("High", "Critical"):
			alerts.append(
				{
					"type": "risk",
					"patient": rs.patient,
					"level": rs.overall_risk_level,
					"message": _("Elevated family risk ({0})").format(rs.overall_risk_level),
				}
			)
	for item in preventive:
		plan_doc = frappe.get_doc("Healthcare Preventive Care Plan", item.name)
		for row in plan_doc.items or []:
			if row.status in ("Due", "Overdue"):
				alerts.append(
					{
						"type": "preventive",
						"patient": item.patient,
						"level": "Medium" if row.status == "Due" else "High",
						"message": _("{0} — {1}").format(row.screening_name, row.status),
					}
				)

	return {
		"family_unit": unit.as_dict(),
		"members": members_detail,
		"open_encounters": open_encounters,
		"chronic_conditions": chronic_conditions,
		"immunizations": immunizations,
		"follow_up_plans": follow_ups,
		"family_history": history,
		"preventive_plans": preventive,
		"risk_scores": risk_scores,
		"alerts": alerts[:15],
	}


@frappe.whitelist()
def get_family_tree(family_unit: str) -> dict:
	"""Genogram data — members linked to hereditary conditions."""
	unit = frappe.get_doc("Healthcare Family Unit", family_unit)
	history = frappe.get_all(
		"Healthcare Family History",
		filters={"family_unit": family_unit},
		fields=[
			"condition_category",
			"condition_description",
			"relative_relationship",
			"patient",
			"age_at_onset",
		],
	)
	nodes: list[dict] = []
	for m in unit.members or []:
		patient = frappe.db.get_value(
			"Healthcare Patient",
			m.patient,
			["patient_name", "gender", "date_of_birth"],
			as_dict=True,
		)
		conditions = [
			h
			for h in history
			if h.patient == m.patient or (h.relative_relationship == "Self" and h.patient == m.patient)
		]
		if not conditions:
			conditions = [h for h in history if h.relative_relationship != "Self" and not h.patient]
		nodes.append(
			{
				"patient": m.patient,
				"name": patient.patient_name if patient else m.patient,
				"gender": patient.gender if patient else "",
				"relationship": m.relationship,
				"conditions": conditions,
			}
		)
	return {
		"family_unit": unit.name,
		"family_name": unit.family_name,
		"head_of_family": unit.head_of_family,
		"shared_genetic_risk_notes": unit.shared_genetic_risk_notes,
		"nodes": nodes,
		"history": history,
	}


@frappe.whitelist()
def migrate_dependents_to_family_units(company: str, branch: str | None = None) -> dict:
	"""Upgrade legacy Healthcare Patient Dependent rows into Healthcare Family Unit households."""
	filters: dict = {"company": company, "is_active": 1}
	dependents = frappe.get_all(
		"Healthcare Patient Dependent",
		filters=filters,
		fields=["name", "guardian_patient", "dependent_patient", "relationship", "branch"],
	)
	if branch:
		dependents = [d for d in dependents if not d.branch or d.branch == branch]

	created = 0
	linked = 0
	seen_guardians: set[str] = set()
	for dep in dependents:
		guardian = dep.guardian_patient
		if guardian in seen_guardians:
			existing = frappe.db.get_value(
				"Healthcare Family Unit",
				{"head_of_family": guardian, "company": company},
				"name",
			)
			if existing:
				link_patient_to_family(existing, dep.dependent_patient, dep.relationship or "Child")
				linked += 1
			continue
		seen_guardians.add(guardian)
		guardian_row = frappe.db.get_value(
			"Healthcare Patient",
			guardian,
			["patient_name", "branch", "company"],
			as_dict=True,
		)
		if not guardian_row:
			continue
		branch_val = branch or dep.branch or guardian_row.branch
		family_number = f"HFU-MIG-{frappe.scrub(guardian)[-8:].upper()}"
		if frappe.db.exists("Healthcare Family Unit", {"family_number": family_number}):
			fu = frappe.db.get_value("Healthcare Family Unit", {"family_number": family_number}, "name")
		else:
			result = create_family_unit(
				family_number=family_number,
				family_name=_("Household of {0}").format(guardian_row.patient_name or guardian),
				head_of_family=guardian,
				company=company,
				branch=branch_val,
				members=[{"patient": guardian, "relationship": "Head", "is_primary_contact": 1}],
			)
			fu = result["name"]
			created += 1
		if dep.dependent_patient != guardian:
			link_patient_to_family(fu, dep.dependent_patient, dep.relationship or "Child")
			linked += 1
	return {"ok": True, "created": created, "linked": linked, "processed": len(dependents)}
