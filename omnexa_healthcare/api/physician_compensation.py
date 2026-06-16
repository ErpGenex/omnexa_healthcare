# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Physician compensation engine — rules, settlements, revenue share."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def list_active_rules(practitioner: str | None = None, branch: str | None = None) -> list[dict]:
	filters: dict = {"is_active": 1}
	if practitioner:
		filters["practitioner"] = practitioner
	if branch:
		filters["branch"] = branch
	return frappe.get_all(
		"Healthcare Physician Compensation Rule",
		filters=filters,
		fields=["name", "rule_code", "practitioner", "compensation_model", "share_percent", "fixed_amount", "branch"],
		order_by="modified desc",
		limit=50,
	)


@frappe.whitelist()
def calculate_settlement_preview(practitioner: str, gross_revenue: float, branch: str | None = None) -> dict:
	filters: dict = {"practitioner": practitioner, "is_active": 1}
	if branch:
		filters["branch"] = branch
	rule = frappe.get_all(
		"Healthcare Physician Compensation Rule",
		filters=filters,
		fields=["compensation_model", "share_percent", "fixed_amount"],
		limit=1,
	)
	if not rule:
		frappe.throw(_("No active compensation rule for practitioner {0}").format(practitioner))
	r = rule[0]
	gross = flt(gross_revenue)
	if r.compensation_model == "Revenue Share" and r.share_percent:
		share = gross * flt(r.share_percent) / 100
	elif r.fixed_amount:
		share = flt(r.fixed_amount)
	else:
		share = 0
	return {"gross_revenue": gross, "physician_share": share, "model": r.compensation_model}
