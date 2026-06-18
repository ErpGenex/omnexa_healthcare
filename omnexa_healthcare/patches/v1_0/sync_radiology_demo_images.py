# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Attach demo radiology preview images to existing reports."""

from __future__ import annotations

import frappe

from omnexa_healthcare.utils.radiology_demo_seed import upgrade_demo_radiology_reports


def execute():
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	branch = frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc") if company else None
	upgrade_demo_radiology_reports(company, branch)
