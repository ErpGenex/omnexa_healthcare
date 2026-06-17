# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Automated care gap detection from cohorts and preventive schedules."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, today


@frappe.whitelist()
def detect_care_gaps(company: str | None = None, branch: str | None = None, limit: int = 50) -> dict:
	"""Scan patients for overdue preventive items and open clinical gaps."""
	limit = min(int(limit or 50), 200)
	filters: dict = {"active": 1}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	patients = frappe.get_all("Healthcare Patient", filters=filters, pluck="name", limit=limit * 2)
	created = 0
	gaps: list[dict] = []

	for patient in patients[:limit]:
		# No recent encounter in 12 months
		last_enc = frappe.db.get_value(
			"Healthcare Encounter", {"patient": patient, "docstatus": 1}, "period_start", order_by="period_start desc"
		)
		if not last_enc or last_enc < add_days(today(), -365):
			gap = _upsert_gap(patient, "Follow-up", "No encounter in 12 months", company, branch)
			if gap:
				created += 1
				gaps.append(gap)

		# Diabetic without recent HbA1c order (proxy: no lab SR in 6 months)
		if frappe.db.exists("Healthcare Clinical Condition", {"patient": patient, "clinical_description": ["like", "%diabet%"]}):
			lab = frappe.db.exists(
				"Healthcare Service Request",
				{"patient": patient, "request_title": ["like", "%HbA1c%"], "creation": [">=", add_days(today(), -180)]},
			)
			if not lab:
				gap = _upsert_gap(patient, "Chronic Care", "Overdue HbA1c for diabetic patient", company, branch)
				if gap:
					created += 1
					gaps.append(gap)

	return {"created": created, "gaps": gaps[:limit]}


def _upsert_gap(patient: str, gap_type: str, description: str, company, branch) -> dict | None:
	if frappe.db.exists("Healthcare Care Gap", {"patient": patient, "description": description, "status": "Open"}):
		return None
	from omnexa_healthcare.api.population_health import create_care_gap

	out = create_care_gap(patient, gap_type, description, due_date=add_days(today(), 30))
	return out


@frappe.whitelist()
def run_care_gap_automation(company: str | None = None, branch: str | None = None) -> dict:
	return detect_care_gaps(company=company, branch=branch)
