# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.api.web_booking import get_published_services
from omnexa_healthcare.utils.branch_demo_seed import (
	reset_healthcare_demo_for_branch,
	seed_healthcare_hospital_demo,
)


class TestHealthcareWebBookingAPI(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		self.branch = frappe.db.get_value("Branch", {"company": self.company}, "name") if self.company else None
		if not (self.company and self.branch):
			self.skipTest("No company/branch for web booking test")
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)
		seed_healthcare_hospital_demo(self.company, self.branch, patients=5, force=1, include_financial=0)

	def tearDown(self):
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)

	def test_get_published_services(self):
		rows = get_published_services(self.company, self.branch)
		self.assertGreaterEqual(len(rows), 8)
		self.assertTrue(all(row.get("service_code") for row in rows))
