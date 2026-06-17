# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe


class TestGapClosureWave12(unittest.TestCase):
	def test_certification_export(self):
		from omnexa_healthcare.api.certification_export import export_certification_pack, get_global_number_one_signoff_pack

		pack = export_certification_pack()
		self.assertIn("certification_records", pack)
		signoff = get_global_number_one_signoff_pack()
		self.assertEqual(signoff.get("mobile_status"), "deferred")

	def test_mobile_deferred_flag(self):
		settings = frappe.get_doc("Healthcare Settings")
		self.assertTrue(getattr(settings, "native_mobile_deferred", 0))

	def test_enterprise_assessment_zero_gaps(self):
		from omnexa_healthcare.enterprise_assessment import get_enterprise_assessment

		data = get_enterprise_assessment()
		self.assertEqual(data["gap_analysis"]["total_open"], 0)
