# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Broaden Healthcare report visibility for clinical, nursing, finance, and desk roles."""

import frappe

REPORT_NAMES = (
	"Healthcare Encounter Summary",
	"Healthcare Appointment Utilization",
	"Healthcare Inpatient Occupancy",
	"Healthcare Appointment Status Summary",
	"Healthcare Admission LOS Analysis",
	"Healthcare Service Charge Summary",
	"Healthcare Diagnostic Category Summary",
)

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


def execute():
	valid_roles = set(frappe.get_all("Role", pluck="name"))
	roles = tuple(r for r in ROLES if r in valid_roles)
	if not roles:
		return

	for name in REPORT_NAMES:
		if not frappe.db.exists("Report", name):
			continue
		doc = frappe.get_doc("Report", name)
		doc.roles = []
		for role in roles:
			doc.append("roles", {"role": role})
		doc.save(ignore_permissions=True)

	frappe.clear_cache()
