# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Population health — cohorts and care gaps."""

from __future__ import annotations

import json

import frappe
from frappe import _


@frappe.whitelist()
def create_cohort(cohort_name: str, criteria: str | dict | None = None, company: str | None = None) -> dict:
	if not cohort_name:
		frappe.throw(_("cohort_name is required"))
	criteria_json = json.dumps(frappe.parse_json(criteria) if criteria else {})
	company = company or frappe.defaults.get_user_default("Company")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Cohort",
			"cohort_name": cohort_name,
			"criteria_json": criteria_json,
			"status": "Active",
			"company": company,
		}
	).insert()
	return {"name": doc.name, "cohort_name": doc.cohort_name}


@frappe.whitelist()
def evaluate_cohort(cohort: str) -> dict:
	cdoc = frappe.get_doc("Healthcare Patient Cohort", cohort)
	criteria = frappe.parse_json(cdoc.criteria_json or "{}")
	filters = {"company": cdoc.company}
	if criteria.get("branch"):
		filters["branch"] = criteria["branch"]
	patients = frappe.get_all("Healthcare Patient", filters=filters, pluck="name", limit=500)
	if criteria.get("min_age"):
		from frappe.utils import getdate, today

		min_age = int(criteria["min_age"])
		cutoff = getdate(today()).replace(year=getdate(today()).year - min_age)
		patients = [
			p
			for p in patients
			if (bd := frappe.db.get_value("Healthcare Patient", p, "birth_date"))
			and getdate(bd) <= cutoff
		]
	return {"cohort": cohort, "patient_count": len(patients), "patients": patients[:100]}


@frappe.whitelist()
def create_care_gap(
	patient: str,
	gap_type: str,
	description: str,
	due_date: str | None = None,
	cohort: str | None = None,
) -> dict:
	if not (patient and gap_type and description):
		frappe.throw(_("patient, gap_type and description are required"))
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Care Gap",
			"patient": patient,
			"cohort": cohort,
			"gap_type": gap_type,
			"description": description,
			"due_date": due_date,
			"status": "Open",
			"company": company,
			"branch": branch,
		}
	).insert()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_open_care_gaps(company: str | None = None, limit: int = 100) -> list[dict]:
	company = company or frappe.defaults.get_user_default("Company")
	return frappe.get_all(
		"Healthcare Care Gap",
		filters={"company": company, "status": ["in", ["Open", "Overdue"]]},
		fields=["name", "patient", "gap_type", "description", "due_date", "status"],
		order_by="due_date asc",
		limit=limit,
	)
