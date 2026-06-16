# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave6_defs import GAP_CLOSURE_WAVE6_DOCTYPES


class TestGapClosureWave6(unittest.TestCase):
	def test_wave6_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE6_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_family_medicine_settings_flag(self):
		settings = frappe.get_doc("Healthcare Settings")
		self.assertTrue(hasattr(settings, "enable_family_medicine"))

	def test_family_unit_api(self):
		from omnexa_healthcare.api.family_unit import get_family_dashboard, list_family_units

		units = list_family_units(limit=5)
		self.assertIsInstance(units, list)
		if units:
			dashboard = get_family_dashboard(units[0].name)
			self.assertIn("members", dashboard)
			self.assertIn("alerts", dashboard)

	def test_family_risk_engine_api(self):
		from omnexa_healthcare.api.family_risk_engine import get_latest_risk_scores

		unit = frappe.get_all("Healthcare Family Unit", limit=1, pluck="name")
		if unit:
			scores = get_latest_risk_scores(unit[0])
			self.assertIsInstance(scores, list)

	def test_family_medicine_pages(self):
		self.assertTrue(frappe.db.exists("Page", "healthcare-family-medicine-dashboard"))
		self.assertTrue(frappe.db.exists("Page", "healthcare-family-tree"))

	def test_fm_physician_role(self):
		self.assertTrue(frappe.db.exists("Role", "FM Physician"))

	def test_enterprise_assessment_family_medicine_domain(self):
		from omnexa_healthcare.enterprise_assessment import compute_maturity_scores

		data = compute_maturity_scores()
		fm = next((d for d in data["domains"] if d["id"] == "family_medicine"), None)
		self.assertIsNotNone(fm)
		self.assertEqual(fm["score"], 100)
