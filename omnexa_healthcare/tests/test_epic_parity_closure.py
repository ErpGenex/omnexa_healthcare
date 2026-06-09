# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Epic parity closure — score gate, DocTypes, APIs."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.healthcare_epic_benchmark import EPIC_PARITY_MATRIX, get_epic_parity_score
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, setup_admin_all_branch_access

EPIC_DOCTYPES = [
	"Healthcare Er Visit",
	"Healthcare In Basket Item",
	"Healthcare Clinical Cds Rule",
	"Healthcare Snomed Code",
	"Healthcare Adt Transfer",
	"Healthcare Nursing Care Plan",
	"Healthcare Discharge Summary",
	"Healthcare Eligibility Check",
	"Healthcare Nphies Claim Bundle",
	"Healthcare Barcode Scan Log",
	"Healthcare Patient Push Notification",
	"Healthcare Clinical Ai Insight",
	"Healthcare Implant Trace",
	"Healthcare Pre Op Checklist",
	"Healthcare Lis Instrument Message",
]

EPIC_PAGES = [
	"healthcare-er-board",
	"healthcare-in-basket",
	"healthcare-physician-mobile",
	"healthcare-patient-mobile",
	"healthcare-dicom-viewer",
]


class TestEpicParityClosure(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def test_epic_parity_score_gate(self):
		score = get_epic_parity_score()
		self.assertGreaterEqual(score["weighted_score"], 4.82)
		self.assertTrue(score["epic_parity_gate"])
		self.assertEqual(score["gaps_closed"], score["gaps_total"])

	def test_matrix_all_domains_at_epic_parity(self):
		for row in EPIC_PARITY_MATRIX:
			self.assertGreaterEqual(row["score"], 4.82, msg=row["id"])

	def test_epic_doctypes_installed(self):
		for dt in EPIC_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", dt), msg=dt)

	def test_epic_pages_installed(self):
		for page in EPIC_PAGES:
			self.assertTrue(frappe.db.exists("Page", page), msg=page)

	def test_er_board_api(self):
		branch = frappe.db.get_value("Branch", {}, "name")
		if not branch:
			self.skipTest("no branch")
		from omnexa_healthcare.api.er import api_get_er_board

		self.assertIsInstance(api_get_er_board(branch), list)

	def test_in_basket_api(self):
		from omnexa_healthcare.api.in_basket import api_get_in_basket

		self.assertIsInstance(api_get_in_basket(), list)

	def test_cds_evaluate_api(self):
		from omnexa_healthcare.api.cds import evaluate_cds

		out = evaluate_cds("Medication Order", {"medication": "penicillin"})
		self.assertIsInstance(out, list)

	def test_physician_mobile_home(self):
		from omnexa_healthcare.api.physician_app import api_physician_home

		out = api_physician_home()
		self.assertIn("appointments_today", out)
		self.assertIn("in_basket", out)

	def test_dicom_viewer_config_api(self):
		report = frappe.db.get_value("Healthcare Diagnostic Report", {}, "name")
		if not report:
			self.skipTest("no diagnostic report")
		from omnexa_healthcare.api.radiology import api_get_dicom_viewer_config

		out = api_get_dicom_viewer_config(report)
		self.assertIsInstance(out, dict)
