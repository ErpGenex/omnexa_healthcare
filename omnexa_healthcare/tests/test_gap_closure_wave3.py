# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave3_defs import GAP_CLOSURE_WAVE3_DOCTYPES


class TestGapClosureWave3(unittest.TestCase):
	def test_wave3_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE3_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_sso_providers(self):
		from omnexa_healthcare.api.enterprise_sso import list_sso_providers

		providers = list_sso_providers()
		self.assertIsInstance(providers, list)

	def test_load_test_benchmark(self):
		from omnexa_healthcare.api.load_test import run_bed_scale_benchmark

		result = run_bed_scale_benchmark(bed_count=500, concurrent_users=10)
		self.assertEqual(result["bed_count"], 500)
		self.assertIn(result["status"], ("Pass", "Pass with notes", "Fail"))

	def test_compliance_himss_jci(self):
		from omnexa_healthcare.compliance_docs import COMPLIANCE_DOCS

		self.assertIn("himss_emram", COMPLIANCE_DOCS)
		self.assertIn("jci_digital", COMPLIANCE_DOCS)

	def test_openehr_export(self):
		enc = frappe.db.get_value("Healthcare Encounter", {}, "name")
		if not enc:
			self.skipTest("No encounter")
		from omnexa_healthcare.api.openehr_bridge import export_openehr_composition

		data = export_openehr_composition(enc)
		self.assertEqual(data["_type"], "COMPOSITION")

	def test_bed_map_page(self):
		self.assertTrue(frappe.db.exists("Page", "healthcare-bed-map"))
