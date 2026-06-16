# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.specialty_engine import seed_default_specialty_modules


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_blood_bank"):
		settings.enable_blood_bank = 1
	if hasattr(settings, "enable_cssd"):
		settings.enable_cssd = 1
	if hasattr(settings, "enable_physician_compensation"):
		settings.enable_physician_compensation = 1
	if hasattr(settings, "enable_quality_capa"):
		settings.enable_quality_capa = 1
	if hasattr(settings, "enable_infection_surveillance"):
		settings.enable_infection_surveillance = 1
	settings.save(ignore_permissions=True)

	created = seed_default_specialty_modules()
	frappe.logger("omnexa_healthcare").info(
		"seed_gap_closure_wave4: world-class modules + settings (%s new modules)", created
	)
