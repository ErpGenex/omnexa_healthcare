# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.workspace.healthcare_workspace import get_workspace_coverage, sync_healthcare_workspace_menu


class TestHealthcareWorkspace(FrappeTestCase):
	def test_workspace_sync_rebuilds(self):
		stats = sync_healthcare_workspace_menu(save=True, rebuild=True)
		self.assertGreater(stats["sections"], 20)
		self.assertGreater(stats["total_links"], 145)
		self.assertGreater(stats["shortcuts"], 145)
		self.assertGreater(stats.get("content_blocks", 0), 160)
		ws = frappe.get_doc("Workspace", "Healthcare")
		breaks = [l for l in ws.links if l.type == "Card Break"]
		self.assertTrue(breaks)
		self.assertTrue(all((l.link_count or 0) > 0 for l in breaks))

	def test_workspace_coverage_counts(self):
		cov = get_workspace_coverage()
		self.assertEqual(cov["healthcare_doctypes_missing"], [])
		self.assertEqual(cov["healthcare_reports_missing"], [])
		self.assertGreaterEqual(cov["pages"], 13)
		self.assertGreaterEqual(cov["reports"], 48)
		self.assertGreaterEqual(cov["doctypes"], 70)

	def test_healthcare_workspace_exists(self):
		self.assertTrue(frappe.db.exists("Workspace", "Healthcare"))

	def test_control_tower_does_not_truncate_sidebar(self):
		"""omnexa_core desk sync must not replace Healthcare with the short HEALTHCARE_DESK layout."""
		sync_healthcare_workspace_menu(save=True, rebuild=True)
		from omnexa_core.install import run_workspace_desk_sync

		run_workspace_desk_sync()
		link_count = frappe.db.count("Workspace Link", {"parent": "Healthcare", "type": "Link"})
		self.assertGreater(link_count, 145, msg=f"Healthcare sidebar truncated to {link_count} links")
