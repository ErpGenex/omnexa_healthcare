# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe


class TestHealthcareRoleDemo(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_role_demo_api_import(self):
		from omnexa_healthcare.api.healthcare_role_demo import ROLE_SPECS, get_healthcare_demo_credentials

		self.assertGreaterEqual(len(ROLE_SPECS), 5)
		creds = get_healthcare_demo_credentials()
		self.assertIn("password", creds)
		self.assertEqual(len(creds["users"]), len(ROLE_SPECS))

	def test_demo_hub_page(self):
		self.assertTrue(frappe.db.exists("Page", "healthcare-demo-hub"))

	def test_app_visibility_boot_inject(self):
		from omnexa_core.omnexa_core.app_visibility import inject_desk_visibility_boot

		boot = {"apps_data": {"apps": [{"name": "omnexa_healthcare"}, {"name": "omnexa_tourism"}]}, "allowed_workspaces": []}
		inject_desk_visibility_boot(boot)
		self.assertIsInstance(boot.get("apps_data", {}).get("apps"), list)
