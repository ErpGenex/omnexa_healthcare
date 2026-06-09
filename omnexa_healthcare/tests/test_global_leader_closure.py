# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Global Leader wave 1 — APIs and score gate."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.healthcare_global_leader import GLOBAL_LEADER_TARGET, get_global_leader_score
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, setup_admin_all_branch_access

GLOBAL_DOCTYPES = [
	"Healthcare Patient Cohort",
	"Healthcare Care Gap",
	"Healthcare Secure Message",
	"Healthcare Ambient Session",
	"Healthcare Voice Dictation",
	"Healthcare Drg Code",
	"Healthcare Mobile Device Token",
	"Healthcare X12 Transaction",
]


class TestGlobalLeaderClosure(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def test_global_leader_score_gate(self):
		score = get_global_leader_score()
		self.assertGreaterEqual(score["weighted_score"], GLOBAL_LEADER_TARGET)
		self.assertTrue(score["global_leader_gate"])

	def test_global_doctypes_installed(self):
		for dt in GLOBAL_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", dt), msg=dt)

	def test_mobile_config_api(self):
		from omnexa_healthcare.api.mobile_api import get_mobile_config

		out = get_mobile_config()
		self.assertIn("pwa_manifest", out)

	def test_x12_270_builds(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		payer = frappe.db.get_value("Healthcare Payer", {}, "name")
		if not (patient and payer):
			self.skipTest("no patient/payer")
		from omnexa_healthcare.api.x12_edi import build_x12_270

		out = build_x12_270(patient, payer, "MEM001")
		self.assertIn("ISA*", out["payload"])

	def test_population_health_cohort(self):
		from omnexa_healthcare.api.population_health import create_cohort, evaluate_cohort

		c = create_cohort("Test Cohort API", criteria={"min_age": 1})
		out = evaluate_cohort(c["name"])
		self.assertIn("patient_count", out)

	def test_westgard_qc(self):
		log = frappe.db.get_value("Healthcare Lab Qc Log", {}, "name")
		if not log:
			self.skipTest("no qc log")
		from omnexa_healthcare.api.lab_qc import evaluate_westgard

		out = evaluate_westgard(log)
		self.assertIn("in_control", out)

	def test_mwl_api(self):
		branch = frappe.db.get_value("Branch", {}, "name")
		if not branch:
			self.skipTest("no branch")
		from omnexa_healthcare.api.radiology import api_get_modality_worklist

		self.assertIsInstance(api_get_modality_worklist(branch), list)

	def test_drg_codes_seeded(self):
		self.assertTrue(frappe.db.exists("Healthcare Drg Code", "470"))
