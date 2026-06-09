# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Broaden Healthcare report visibility for clinical, nursing, finance, and desk roles."""

from __future__ import annotations

import json
import os

import frappe

ROLES = (
	"System Manager",
	"Company Admin",
	"Desk User",
	"Report Manager",
	"Accounts Manager",
	"Accounts User",
	"Physician",
	"Nursing User",
)


def _discover_report_names() -> list[str]:
	report_dir = frappe.get_app_path("omnexa_healthcare", "omnexa_healthcare", "report")
	names: list[str] = []
	if not os.path.isdir(report_dir):
		return names
	for folder in sorted(os.listdir(report_dir)):
		json_path = os.path.join(report_dir, folder, f"{folder}.json")
		if not os.path.isfile(json_path):
			continue
		with open(json_path, encoding="utf-8") as handle:
			data = json.load(handle)
		if data.get("name"):
			names.append(data["name"])
	return names


def execute():
	valid_roles = set(frappe.get_all("Role", pluck="name"))
	roles = tuple(r for r in ROLES if r in valid_roles)
	if not roles:
		return

	for name in _discover_report_names():
		if not frappe.db.exists("Report", name):
			continue
		doc = frappe.get_doc("Report", name)
		doc.roles = []
		for role in roles:
			doc.append("roles", {"role": role})
		doc.save(ignore_permissions=True)

	frappe.clear_cache()
