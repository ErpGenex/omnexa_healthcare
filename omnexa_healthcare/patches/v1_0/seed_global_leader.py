# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Seed DRG codes and sample population health cohort."""

import frappe

DRG = [
	("470", "Major hip and knee joint replacement", 1.8, 15000),
	("291", "Heart failure and shock", 1.2, 12000),
	("193", "Simple pneumonia and pleurisy", 0.9, 8000),
	("392", "Esophagitis gastrointestinal disorders", 0.7, 6000),
]


def execute():
	for code, desc, weight, rate in DRG:
		if frappe.db.exists("Healthcare Drg Code", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Healthcare Drg Code",
				"drg_code": code,
				"description": desc,
				"weight": weight,
				"base_rate": rate,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Healthcare Patient Cohort", {"cohort_name": "Diabetes Chronic Care"}):
		company = frappe.db.get_value("Company", {}, "name")
		if company:
			frappe.get_doc(
				{
					"doctype": "Healthcare Patient Cohort",
					"cohort_name": "Diabetes Chronic Care",
					"description": "Patients with diabetes for care gap outreach",
					"criteria_json": '{"min_age": 18}',
					"status": "Active",
					"company": company,
				}
			).insert(ignore_permissions=True)
