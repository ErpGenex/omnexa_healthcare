# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave7_defs import GAP_CLOSURE_WAVE7_DOCTYPES


class TestGapClosureWave7(unittest.TestCase):
	def test_wave7_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE7_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_erx_settings(self):
		self.assertTrue(hasattr(frappe.get_doc("Healthcare Settings"), "enable_erx"))

	def test_rxnorm_seeded(self):
		count = frappe.db.count("Healthcare Rxnorm Code", {"is_active": 1})
		self.assertGreaterEqual(count, 1000)

	def test_erx_api(self):
		from omnexa_healthcare.api.erx import search_drugs

		rows = search_drugs("metformin")
		self.assertIsInstance(rows, list)

	def test_erx_pages(self):
		self.assertTrue(frappe.db.exists("Page", "healthcare-erx-writer"))
		self.assertTrue(frappe.db.exists("Page", "healthcare-pharmacy-rx-verify"))
