# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Clinical Decision Support at order entry."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def evaluate_cds(trigger_event: str, context: str | dict) -> list[dict]:
	data = frappe.parse_json(context) if isinstance(context, str) else (context or {})
	rules = frappe.get_all(
		"Healthcare Clinical Cds Rule",
		filters={"is_active": 1, "trigger_event": trigger_event},
		fields=["rule_name", "match_field", "severity", "message"],
	)
	alerts = []
	value = str(data.get("value") or data.get("item") or data.get("medication") or data.get("code") or "")
	for rule in rules:
		if rule.match_field and rule.match_field not in value:
			continue
		alerts.append(rule)
		if rule.severity == "Contraindicated":
			break
	return alerts


@frappe.whitelist()
def evaluate_medication_order(patient: str, medication: str) -> list[dict]:
	from omnexa_healthcare.api.pharmacy import api_check_drug_interactions

	alerts = list(evaluate_cds("Medication Order", {"value": medication}))
	alerts.extend(api_check_drug_interactions(patient, medication) or [])
	return alerts
