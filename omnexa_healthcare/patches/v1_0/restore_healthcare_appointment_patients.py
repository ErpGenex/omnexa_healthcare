# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Create Healthcare Patient from legacy appointment names after schema adds `patient` link."""

import frappe


def execute():
	if not frappe.db.table_exists("_omx_health_appt_legacy"):
		return
	if not frappe.db.table_exists("tabHealthcare Appointment"):
		frappe.db.sql("DROP TABLE IF EXISTS `_omx_health_appt_legacy`")
		frappe.db.commit()
		return
	if not frappe.db.has_column("tabHealthcare Appointment", "patient"):
		frappe.db.sql("DROP TABLE IF EXISTS `_omx_health_appt_legacy`")
		frappe.db.commit()
		return

	rows = frappe.db.sql(
		"SELECT appt_name, patient_name, company, branch FROM `_omx_health_appt_legacy`",
		as_dict=True,
	)
	for row in rows:
		if not frappe.db.exists("Healthcare Appointment", row.appt_name):
			continue
		existing = frappe.db.get_value("Healthcare Appointment", row.appt_name, "patient")
		if existing:
			continue
		pname = (row.patient_name or "").strip() or "Legacy Patient"
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": row.company,
				"branch": row.branch,
				"given_name": pname[:140],
				"family_name": "Unknown",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "Other",
						"type_display": "Migrated from appointment",
						"value": f"LEGACY-{row.appt_name}"[:140],
						"is_primary_mrn": 0,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Healthcare Appointment", row.appt_name, "patient", doc.name, update_modified=False)
		if frappe.db.has_column("tabHealthcare Appointment", "naming_series"):
			frappe.db.set_value(
				"Healthcare Appointment",
				row.appt_name,
				"naming_series",
				"HAP-.#####",
				update_modified=False,
			)

	frappe.db.sql("DROP TABLE IF EXISTS `_omx_health_appt_legacy`")
	frappe.db.commit()
