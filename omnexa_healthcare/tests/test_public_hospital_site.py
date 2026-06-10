# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.api.public_hospital_site import (
	build_public_urls,
	get_published_departments,
	get_published_doctors,
	get_site_config,
	get_site_urls,
)
from omnexa_healthcare.utils.branch_demo_seed import (
	reset_healthcare_demo_for_branch,
	seed_healthcare_hospital_demo,
)


class TestPublicHospitalSite(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		self.branch = frappe.db.get_value("Branch", {"company": self.company}, "name") if self.company else None
		if not (self.company and self.branch):
			self.skipTest("No company/branch for hospital site test")
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)
		seed_healthcare_hospital_demo(self.company, self.branch, patients=5, force=1, include_financial=0)

	def tearDown(self):
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)

	def test_get_site_config_by_branch(self):
		cfg = get_site_config(branch=self.branch)
		self.assertEqual(cfg["branch"], self.branch)
		self.assertEqual(cfg["company"], self.company)
		self.assertIn("urls", cfg)
		self.assertTrue(cfg["hospital_name_ar"])

	def test_get_site_config_by_slug(self):
		slug = frappe.db.get_value("Healthcare Branch Website", self.branch, "site_slug")
		self.assertTrue(slug)
		cfg = get_site_config(site=slug)
		self.assertEqual(cfg["branch"], self.branch)

	def test_published_departments_and_doctors(self):
		depts = get_published_departments(branch=self.branch)
		docs = get_published_doctors(branch=self.branch)
		self.assertGreaterEqual(len(depts), 4)
		self.assertGreaterEqual(len(docs), 3)
		self.assertTrue(all(d.get("department_name") for d in depts))

	def test_site_urls_for_desk(self):
		frappe.set_user("Administrator")
		urls = get_site_urls(self.branch)
		self.assertIn("/hospital", urls["public_url"])
		self.assertIn("booking", urls["urls"])

	def test_build_public_urls(self):
		urls = build_public_urls(branch=self.branch, site_slug="demo-site")
		self.assertIn("site=demo-site", urls["home"])
		self.assertIn("site=demo-site", urls["booking"])
