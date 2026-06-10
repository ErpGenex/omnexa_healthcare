# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import json

import frappe

from omnexa_healthcare.follow_up_templates import FOLLOW_UP_PLAN_TEMPLATES
from omnexa_healthcare.specialty_engine import seed_default_specialty_modules


def execute():
	seed_default_specialty_modules()
	for module_code, cfg in FOLLOW_UP_PLAN_TEMPLATES.items():
		if not frappe.db.exists("Healthcare Specialty Module", module_code):
			continue
		frappe.db.set_value(
			"Healthcare Specialty Module",
			module_code,
			"follow_up_workflow",
			json.dumps(cfg),
		)
	frappe.db.commit()
