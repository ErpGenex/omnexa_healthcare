# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave9_defs import GAP_CLOSURE_WAVE9_DOCTYPES, PHI_AUDIT_DOCTYPES


class TestGapClosureWave9(unittest.TestCase):
	def test_wave9_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE9_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_phi_doctype_coverage(self):
		self.assertGreaterEqual(len(PHI_AUDIT_DOCTYPES), 26)

	def test_gdpr_api(self):
		from omnexa_healthcare.api.gdpr_erasure import get_compliance_templates

		templates = get_compliance_templates()
		self.assertIn("baa_template", templates)
		self.assertIn("dpia_template", templates)

	def test_security_settings(self):
		settings = frappe.get_doc("Healthcare Settings")
		self.assertTrue(hasattr(settings, "enforce_mfa_hard_block"))
