# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Refresh Healthcare Specialty Module follow-up workflows from code templates."""

import json

import frappe

from omnexa_healthcare.follow_up_templates import FOLLOW_UP_PLAN_TEMPLATES


def execute():
	for module_code, cfg in FOLLOW_UP_PLAN_TEMPLATES.items():
		if not cfg.get("supports_multi_visit"):
			continue
		if not frappe.db.exists("Healthcare Specialty Module", module_code):
			continue
		frappe.db.set_value(
			"Healthcare Specialty Module",
			module_code,
			"follow_up_workflow",
			json.dumps(cfg),
		)
	frappe.db.commit()
