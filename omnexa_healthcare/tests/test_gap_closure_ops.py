# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Operational gap closure — ICD-10 on diagnosis, observation UCUM, roster, claims."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.observation_profiles import default_ucum_for_profile
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, setup_admin_all_branch_access


class TestGapClosureOps(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def test_observation_ucum_defaults(self):
		self.assertEqual(default_ucum_for_profile("heart_rate"), "/min")
		self.assertEqual(default_ucum_for_profile("blood_pressure"), "mm[Hg]")

	def test_encounter_diagnosis_icd10_validation(self):
		if not frappe.db.exists("Healthcare Icd10 Code", {"code": "I10"}):
			self.skipTest("ICD-10 I10 not seeded")
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		company = frappe.db.get_value("Company", {}, "name")
		branch = frappe.db.get_value("Branch", {}, "name")
		if not (patient and company and branch):
			self.skipTest("missing master data")
		enc = frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": patient,
				"company": company,
				"branch": branch,
				"status": "in-progress",
				"period_start": frappe.utils.now_datetime(),
				"diagnoses": [{"icd10_code": "I10", "description": "Pending"}],
			}
		)
		enc.insert(ignore_permissions=True)
		dx = enc.diagnoses[0]
		self.assertIn("hypertension", (dx.description or "").lower())

	def test_practitioner_roster_api(self):
		from omnexa_healthcare.api.scheduling import api_get_practitioner_roster

		self.assertIsInstance(api_get_practitioner_roster(), list)

	def test_insurance_claim_workflow(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		company = frappe.db.get_value("Company", {}, "name")
		branch = frappe.db.get_value("Branch", {}, "name")
		payer = frappe.db.get_value("Healthcare Payer", {}, "name")
		plan = frappe.db.get_value("Healthcare Insurance Plan", {}, "name")
		if not all([patient, company, branch, payer, plan]):
			self.skipTest("RCM masters missing")
		claim = frappe.get_doc(
			{
				"doctype": "Healthcare Insurance Claim",
				"patient": patient,
				"payer": payer,
				"insurance_plan": plan,
				"claim_amount": 500,
				"company": company,
				"branch": branch,
			}
		).insert(ignore_permissions=True)
		claim.submit_claim()
		self.assertEqual(claim.status, "Submitted")
		claim.approve_claim(approved_amount=400)
		self.assertEqual(claim.status, "Approved")
		self.assertEqual(claim.approved_amount, 400)
