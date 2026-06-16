# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Quality management — CAPA, infection surveillance, QMS dashboard."""

from __future__ import annotations

import frappe
from frappe.utils import today


@frappe.whitelist()
def list_open_capa(branch: str | None = None, company: str | None = None) -> list[dict]:
	filters: dict = {"status": ["in", ["Draft", "In Progress", "Under Review"]]}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Healthcare Quality Corrective Action",
		filters=filters,
		fields=["name", "title", "severity", "status", "due_date", "branch"],
		order_by="due_date asc",
		limit=50,
	)


@frappe.whitelist()
def list_active_infection_cases(branch: str | None = None) -> list[dict]:
	filters: dict = {"status": ["in", ["Open", "Under Surveillance", "Investigating"]]}
	if branch:
		filters["branch"] = branch
	return frappe.get_all(
		"Healthcare Infection Surveillance Case",
		filters=filters,
		fields=["name", "patient", "infection_type", "onset_date", "status", "isolation_required"],
		order_by="onset_date desc",
		limit=50,
	)


@frappe.whitelist()
def qms_dashboard(branch: str | None = None, company: str | None = None) -> dict:
	return {
		"open_capa": len(list_open_capa(branch=branch, company=company)),
		"active_infections": len(list_active_infection_cases(branch=branch)),
		"overdue_capa": frappe.db.count(
			"Healthcare Quality Corrective Action",
			{"status": ["in", ["In Progress", "Under Review"]], "due_date": ["<", today()], **({"branch": branch} if branch else {})},
		),
	}
