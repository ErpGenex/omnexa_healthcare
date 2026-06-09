# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared helpers for Healthcare script reports."""

from __future__ import annotations

import frappe
from frappe import _
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def require_company(filters) -> frappe._dict:
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))
	return filters


def branch_conditions(filters, table_alias: str = "") -> tuple[list[str], frappe._dict]:
	prefix = f"{table_alias}." if table_alias else ""
	conditions = [f"{prefix}company = %(company)s"]
	if filters.get("branch"):
		conditions.append(f"{prefix}branch = %(branch)s")
	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return ["1=0"], filters
		filters.allowed_branches = tuple(allowed)
		conditions.append(f"{prefix}branch in %(allowed_branches)s")
	return conditions, filters


def date_conditions(filters, date_field: str, table_alias: str = "") -> list[str]:
	prefix = f"{table_alias}." if table_alias else ""
	conditions = []
	if filters.get("from_date"):
		conditions.append(f"DATE({prefix}{date_field}) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append(f"DATE({prefix}{date_field}) <= %(to_date)s")
	return conditions


STANDARD_FILTERS = [
	{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
	{"fieldname": "branch", "fieldtype": "Link", "label": "Branch", "options": "Branch"},
	{"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1},
	{"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1},
]

STANDARD_ROLES = [
	"System Manager",
	"Company Admin",
	"Desk User",
	"Report Manager",
	"Physician",
	"Nursing User",
]
