# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.specialty_engine import seed_default_specialty_modules


def execute():
	created = seed_default_specialty_modules()
	msg = f"seed_specialty_modules: created {created} modules" if created else "seed_specialty_modules: already seeded"
	frappe.logger("omnexa_healthcare").info(msg)
