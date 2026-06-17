# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave8_defs import DEFAULT_CDS_RULES, SNOMED_WAVE8_SUBSET


class TestGapClosureWave8(unittest.TestCase):
	def test_cds_rules_seeded(self):
		for name, _t, _m, _s in DEFAULT_CDS_RULES:
			self.assertTrue(frappe.db.exists("Healthcare Clinical Cds Rule", {"rule_name": name}), name)

	def test_snomed_subset(self):
		for cid, _term in SNOMED_WAVE8_SUBSET:
			self.assertTrue(frappe.db.exists("Healthcare Snomed Code", {"concept_id": cid}), cid)

	def test_evaluate_erx_cds(self):
		from omnexa_healthcare.api.cds import evaluate_erx_cds

		patient = frappe.get_all("Healthcare Patient", limit=1, pluck="name")
		if patient:
			alerts = evaluate_erx_cds(patient[0], [{"drug_name": "Metformin"}])
			self.assertIsInstance(alerts, list)

	def test_advanced_cds_flag(self):
		self.assertTrue(hasattr(frappe.get_doc("Healthcare Settings"), "enable_advanced_cds"))
