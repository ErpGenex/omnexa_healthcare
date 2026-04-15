# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

"""Run before model sync when upgrading from free-text patient_name on appointments."""

import frappe


def execute():
	if not frappe.db.table_exists("tabHealthcare Appointment"):
		return
	if not frappe.db.has_column("tabHealthcare Appointment", "patient_name"):
		return

	frappe.db.sql("DROP TABLE IF EXISTS `_omx_health_appt_legacy`")
	frappe.db.sql(
		"""
		CREATE TABLE `_omx_health_appt_legacy` (
			appt_name VARCHAR(140) PRIMARY KEY,
			patient_name TEXT,
			company VARCHAR(140),
			branch VARCHAR(140)
		)
		"""
	)
	frappe.db.sql(
		"""
		INSERT INTO `_omx_health_appt_legacy` (appt_name, patient_name, company, branch)
		SELECT name, patient_name, company, branch
		FROM `tabHealthcare Appointment`
		"""
	)
	frappe.db.commit()
