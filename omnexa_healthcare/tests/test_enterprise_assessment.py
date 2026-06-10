# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.enterprise_assessment import (
	compute_maturity_scores,
	get_enterprise_assessment,
	run_functional_audit,
	run_security_audit,
)


class TestEnterpriseAssessment(unittest.TestCase):
	def test_functional_audit_counts(self):
		audit = run_functional_audit()
		self.assertGreaterEqual(audit["counts"]["doctypes"], 70)
		self.assertGreaterEqual(audit["counts"]["reports"], 40)
		self.assertTrue(audit["backward_compatible"])

	def test_maturity_scores(self):
		maturity = compute_maturity_scores()
		self.assertGreater(maturity["weighted_score"], 50)
		self.assertGreaterEqual(len(maturity["domains"]), 15)

	def test_security_audit(self):
		security = run_security_audit()
		self.assertGreaterEqual(security["score"], 40)
		self.assertTrue(security["checks"]["phi_access_log"])

	def test_whitelisted_assessment_api(self):
		out = get_enterprise_assessment()
		self.assertEqual(out["app"], "omnexa_healthcare")
		self.assertIn("world_class_readiness_score", out)
		self.assertIn("gap_analysis", out)
		self.assertTrue(out["backward_compatible"])
		self.assertGreaterEqual(out["competitive_rank"], 1)
