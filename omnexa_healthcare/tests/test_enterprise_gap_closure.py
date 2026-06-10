# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.api.patient_journey import get_patient_journey
from omnexa_healthcare.compliance_docs import COMPLIANCE_DOCS
from omnexa_healthcare.enterprise_assessment import get_enterprise_assessment
from omnexa_healthcare.specialty_engine import list_specialty_modules


class TestEnterpriseGapClosure(unittest.TestCase):
	def test_all_strategic_gaps_closed(self):
		assessment = get_enterprise_assessment()
		gaps = assessment["gap_analysis"]
		self.assertEqual(gaps["total_open"], 0)
		for item in gaps["strategic_gaps"]:
			self.assertEqual(item["status"], "completed")

	def test_world_class_score_five(self):
		assessment = get_enterprise_assessment()
		self.assertGreaterEqual(assessment["world_class_readiness_score"], 5.0)
		self.assertGreaterEqual(assessment["ux"]["ux_score"], 90)

	def test_fifteen_specialty_modules(self):
		modules = list_specialty_modules()
		self.assertGreaterEqual(len(modules), 15)

	def test_hipaa_gdpr_docs(self):
		self.assertIn("hipaa", COMPLIANCE_DOCS)
		self.assertIn("gdpr", COMPLIANCE_DOCS)

	def test_patient_journey_e2e(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("No patient")
		journey = get_patient_journey(patient)
		self.assertEqual(len(journey["steps"]), 9)
		self.assertIn("progress_pct", journey)

	def test_new_doctypes_exist(self):
		for dt in (
			"Healthcare Dental Treatment Plan",
			"Healthcare Orthodontic Case",
			"Healthcare Installment Plan",
			"Healthcare Treatment Package",
		):
			self.assertTrue(frappe.db.exists("DocType", dt))

	def test_new_pages_exist(self):
		for page in ("healthcare-dental-chart", "healthcare-specialty-wizard", "healthcare-patient-journey"):
			self.assertTrue(frappe.db.exists("Page", page))
