# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.gap_closure_wave13_defs import GAP_CLOSURE_WAVE13_CHECKS, GAP_CLOSURE_WAVE13_DOCTYPES


class TestGapClosureWave13(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Healthcare Settings", "enable_patient_otp", 1)
		self.company = frappe.defaults.get_user_default("Company") or frappe.get_all("Company", limit=1, pluck="name")[0]
		self.branch = frappe.defaults.get_user_default("Branch") or frappe.get_all("Branch", limit=1, pluck="name")[0]
		frappe.defaults.set_user_default("Branch", self.branch, "Administrator")

	def test_wave13_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE13_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_patient_registration_fields(self):
		meta = frappe.get_meta("Healthcare Patient")
		self.assertTrue(meta.has_field("registration_status"))
		self.assertTrue(meta.has_field("portal_user"))

	def test_register_patient_full_reception(self):
		from omnexa_healthcare.api.patient_registration import register_patient_full

		import random

		suffix = random.randint(100000, 999999)
		res = register_patient_full(
			{
				"given_name": "Test",
				"family_name": f"Patient{suffix}",
				"gender": "male",
				"birth_date": "1990-01-01",
				"phone": f"010{suffix}",
				"national_id": f"288{suffix:011d}"[:14],
				"company": self.company,
				"branch": self.branch,
			}
		)
		self.assertIn("patient", res)
		status = frappe.db.get_value("Healthcare Patient", res["patient"], "registration_status")
		self.assertIn(status, ("Complete", "Verified"))

	def test_booking_gate_blocks_incomplete(self):
		from omnexa_healthcare.api.patient_registration import assert_booking_allowed

		patient = frappe.get_all("Healthcare Patient", filters={"registration_status": "Incomplete"}, limit=1, pluck="name")
		if patient:
			with self.assertRaises(Exception):
				assert_booking_allowed(patient[0], online=False)

	def test_device_integration(self):
		from omnexa_healthcare.api.device_integration import ingest_device_vitals, register_medical_device

		reg = register_medical_device("VSM-TEST-001", "Test Vitals Monitor", company=self.company, branch=self.branch)
		patient = frappe.get_all("Healthcare Patient", limit=1, pluck="name")
		if not patient:
			self.skipTest("No patient")
		result = ingest_device_vitals(
			patient[0],
			"VSM-TEST-001",
			{"heart_rate": 72, "bp_systolic": 120, "bp_diastolic": 80},
			company=self.company,
			branch=self.branch,
		)
		self.assertGreaterEqual(result["count"], 1)

	def test_fhir_device_read(self):
		from omnexa_healthcare.api.device_integration import register_medical_device
		from omnexa_healthcare.api.fhir_rest import fhir_read

		reg = register_medical_device("FHIR-DEV-001", "FHIR Test Device", company=self.company, branch=self.branch)
		bundle = fhir_read("Device", reg["device"])
		self.assertEqual(bundle["resourceType"], "Device")

	def test_specialty_modules_expanded(self):
		from omnexa_healthcare.specialty_engine import DEFAULT_SPECIALTY_MODULES

		codes = {m["module_code"] for m in DEFAULT_SPECIALTY_MODULES}
		for code in ("plastic_surgery", "geriatrics", "pathology", "interventional_radiology"):
			self.assertIn(code, codes)

	def test_gap13_checks(self):
		for check in GAP_CLOSURE_WAVE13_CHECKS:
			if check.startswith("omnexa_"):
				__import__(check)
			elif frappe.db.exists("DocType", check):
				pass
			elif frappe.db.has_column("Healthcare Patient", check):
				pass
			else:
				self.fail(f"Missing check target: {check}")

	def test_enterprise_assessment_wave13(self):
		from omnexa_healthcare.enterprise_assessment import compute_maturity_scores

		data = compute_maturity_scores()
		px = next((d for d in data["domains"] if d["id"] == "patient_experience"), None)
		self.assertIsNotNone(px)
		self.assertGreaterEqual(px["score"], 90)
