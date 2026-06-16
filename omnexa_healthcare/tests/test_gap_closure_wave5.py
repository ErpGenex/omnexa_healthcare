# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave5_defs import DEFAULT_ICD11_CODES, GAP_CLOSURE_WAVE5_DOCTYPES


class TestGapClosureWave5(unittest.TestCase):
	def test_wave5_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE5_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_icd11_seeded(self):
		for code, desc, _chapter, _icd10 in DEFAULT_ICD11_CODES[:3]:
			self.assertTrue(frappe.db.exists("Healthcare Icd11 Code", code), code)

	def test_icd11_api(self):
		from omnexa_healthcare.api.icd11 import map_icd11_to_icd10, search_icd11_codes

		rows = search_icd11_codes("diabetes")
		self.assertIsInstance(rows, list)
		if frappe.db.exists("Healthcare Icd11 Code", "5A11"):
			mapped = map_icd11_to_icd10("5A11")
			self.assertEqual(mapped["icd10"], "E11")

	def test_blood_bank_api(self):
		from omnexa_healthcare.api.blood_bank import list_available_units

		units = list_available_units()
		self.assertIsInstance(units, list)

	def test_enterprise_assessment_zero_gaps(self):
		from omnexa_healthcare.enterprise_assessment import get_enterprise_assessment

		data = get_enterprise_assessment()
		self.assertEqual(data["gap_analysis"]["total_open"], 0)
