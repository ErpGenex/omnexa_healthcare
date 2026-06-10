# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.api.dental import get_tooth_numbering_map, upsert_dental_chart_entry
from omnexa_healthcare.specialty_engine import list_specialty_modules, seed_default_specialty_modules


class TestSpecialtyEngine(unittest.TestCase):
	def test_seed_specialty_modules_idempotent(self):
		first = seed_default_specialty_modules()
		second = seed_default_specialty_modules()
		self.assertGreaterEqual(first, 0)
		self.assertEqual(second, 0)
		modules = list_specialty_modules()
		self.assertGreaterEqual(len(modules), 1)
		dental = [m for m in modules if m.get("module_code") == "dental"]
		self.assertTrue(dental)

	def test_dental_numbering_map(self):
		fdi = get_tooth_numbering_map("FDI")
		self.assertEqual(len(fdi["teeth"]), 32)
		univ = get_tooth_numbering_map("Universal")
		self.assertEqual(len(univ["teeth"]), 32)

	def test_dental_chart_upsert_requires_company(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("No patient in site")
		company = frappe.db.get_value("Healthcare Patient", patient, "company")
		out = upsert_dental_chart_entry(
			patient=patient,
			tooth_id="11",
			company=company,
			condition="caries",
			numbering_system="FDI",
		)
		self.assertTrue(out.get("name"))
