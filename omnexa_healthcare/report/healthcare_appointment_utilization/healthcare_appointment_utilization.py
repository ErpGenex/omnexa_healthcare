# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["a.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("a.appointment_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("a.appointment_date <= %(to_date)s")

	data = frappe.db.sql(
		f"""
		SELECT
			DATE(a.appointment_date) AS posting_date,
			COUNT(*) AS appointments
		FROM `tabHealthcare Appointment` a
		WHERE {' AND '.join(conditions)}
		GROUP BY DATE(a.appointment_date)
		ORDER BY posting_date DESC
		""",
		filters,
		as_dict=True,
	)
	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": _("Appointments"), "fieldname": "appointments", "fieldtype": "Int", "width": 140},
	]
	return columns, data
