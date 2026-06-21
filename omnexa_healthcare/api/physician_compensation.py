# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Physician compensation engine — rules, settlements, revenue share."""

from __future__ import annotations

import frappe

from omnexa_healthcare.api.physician_compensation_engine import (
	calculate_settlement_preview,
	get_practitioner_ledger_summary,
	list_active_rules,
)

__all__ = [
	"list_active_rules",
	"calculate_settlement_preview",
	"get_practitioner_ledger_summary",
]


def list_active_rules(practitioner: str | None = None, branch: str | None = None) -> list[dict]:
	filters: dict = {"is_active": 1}
	if practitioner:
		filters["practitioner"] = practitioner
	if branch:
		filters["branch"] = branch
	return frappe.get_all(
		"Healthcare Physician Compensation Rule",
		filters=filters,
		fields=[
			"name",
			"rule_code",
			"practitioner",
			"compensation_model",
			"share_percent",
			"fixed_amount",
			"branch",
			"specialty",
			"priority",
		],
		order_by="priority desc, modified desc",
		limit=50,
	)
