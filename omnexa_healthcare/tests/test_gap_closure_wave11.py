# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe


class TestGapClosureWave11(unittest.TestCase):
	def test_predictive_v2(self):
		from omnexa_healthcare.api.predictive_analytics import get_predictive_dashboard, predict_readmission_risk

		dash = get_predictive_dashboard()
		self.assertEqual(dash.get("readmission_model"), "erpgenex-readmit-v2")
		patient = frappe.get_all("Healthcare Patient", limit=1, pluck="name")
		if patient:
			risk = predict_readmission_risk(patient[0])
			self.assertEqual(risk.get("model"), "erpgenex-readmit-v2")

	def test_care_gap_automation(self):
		from omnexa_healthcare.api.care_gap_automation import detect_care_gaps

		out = detect_care_gaps(limit=5)
		self.assertIn("gaps", out)

	def test_bi_settings(self):
		settings = frappe.get_doc("Healthcare Settings")
		self.assertTrue(hasattr(settings, "enable_care_gap_automation"))
