# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.utils.branch_demo_seed import (
	reset_healthcare_demo_for_branch,
	seed_healthcare_hospital_demo,
)


class TestHealthcareBranchDemoSeed(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		self.branch = frappe.db.get_value("Branch", {"company": self.company}, "name") if self.company else None
		if not (self.company and self.branch):
			self.skipTest("No company/branch for healthcare demo test")

	def tearDown(self):
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)

	def test_seed_includes_web_services_and_bookings(self):
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)
		result = seed_healthcare_hospital_demo(
			self.company,
			self.branch,
			patients=20,
			force=1,
			include_financial=0,
		)
		self.assertTrue(result.get("ok"))
		self.assertGreaterEqual(result.get("published_services", 0), 8)
		self.assertGreaterEqual(result.get("web_bookings", 0), 10)
		self.assertGreaterEqual(result.get("specialty_modules", 0), 15)
		self.assertGreaterEqual(result.get("dental_charts", 0), 5)
		self.assertGreaterEqual(result.get("treatment_plans", 0), 3)
		self.assertGreaterEqual(result.get("follow_up_plans", 0), 12)

		published = frappe.db.count(
			"Healthcare Service Catalog",
			{"company": self.company, "branch": self.branch, "publish_on_website": 1},
		)
		self.assertGreaterEqual(published, 8)

		web_appts = frappe.db.count(
			"Healthcare Appointment",
			{"company": self.company, "branch": self.branch, "booking_channel": "Website"},
		)
		self.assertGreaterEqual(web_appts, 10)

		self.assertTrue(frappe.db.exists("Web Page", {"title": ["like", "DEMO-HC-%"]}))
