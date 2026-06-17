# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.api import journey_desk


class TestJourneyDesk(unittest.TestCase):
	def setUp(self):
		self.company = frappe.defaults.get_user_default("Company") or frappe.get_all("Company", limit=1, pluck="name")[0]
		self.branch = frappe.defaults.get_user_default("Branch") or frappe.get_all("Branch", limit=1, pluck="name")[0]

	def test_journey_pages_exist(self):
		for page in (
			"healthcare-reception-desk",
			"healthcare-cashier-desk",
			"healthcare-physician-workbench",
			"healthcare-patient-consumer",
		):
			self.assertTrue(frappe.db.exists("Page", page), page)

	def test_reception_kpis(self):
		kpis = journey_desk.get_reception_kpis(self.company, self.branch)
		self.assertIn("appointments_today", kpis)
		self.assertIn("revenue_today", kpis)
		self.assertIn("avg_wait_mins", kpis)

	def test_reception_clinics(self):
		clinics = journey_desk.get_reception_clinics(self.company, self.branch)
		self.assertIsInstance(clinics, list)

	def test_reception_doctors(self):
		doctors = journey_desk.get_reception_doctors(self.company, self.branch)
		self.assertIsInstance(doctors, list)

	def test_search_patient_quick_short_query(self):
		self.assertEqual(journey_desk.search_patient_quick("a", self.branch), [])

	def test_cashier_queue(self):
		rows = journey_desk.get_cashier_queue(self.company, self.branch)
		self.assertIsInstance(rows, list)

	def test_patient_journey_online(self):
		data = journey_desk.get_patient_journey_online(self.company, self.branch)
		self.assertEqual(data["steps"], 8)
		self.assertIn("clinics", data)

	def test_journey_token_format(self):
		token = journey_desk._journey_token("APT-TEST-001", "PAT-001")
		self.assertTrue(token.startswith("JRN-"))

	def test_physician_workbench_with_patient(self):
		patient = frappe.get_all("Healthcare Patient", limit=1, pluck="name")
		if not patient:
			self.skipTest("No patient in site")
		data = journey_desk.get_physician_workbench(patient[0])
		self.assertIn("vitals", data)
		self.assertIn("chart", data)

	def test_enterprise_assessment_patient_experience(self):
		from omnexa_healthcare.enterprise_assessment import compute_maturity_scores

		data = compute_maturity_scores()
		px = next((d for d in data["domains"] if d["id"] == "patient_experience"), None)
		self.assertIsNotNone(px)
