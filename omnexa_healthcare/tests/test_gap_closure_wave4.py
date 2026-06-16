# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave4_defs import GAP_CLOSURE_WAVE4_DOCTYPES


class TestGapClosureWave4(unittest.TestCase):
	def test_wave4_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE4_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_world_class_settings_flags(self):
		settings = frappe.get_doc("Healthcare Settings")
		for field in (
			"enable_blood_bank",
			"enable_cssd",
			"enable_physician_compensation",
			"enable_quality_capa",
			"enable_infection_surveillance",
		):
			self.assertTrue(hasattr(settings, field), field)

	def test_specialty_module_count(self):
		count = frappe.db.count("Healthcare Specialty Module", {"is_active": 1})
		self.assertGreaterEqual(count, 28)
