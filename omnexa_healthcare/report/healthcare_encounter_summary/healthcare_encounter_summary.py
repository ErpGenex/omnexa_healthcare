# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["e.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("e.encounter_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("e.encounter_date <= %(to_date)s")

	data = frappe.db.sql(
		f"""
		SELECT
			DATE(e.encounter_date) AS posting_date,
			COUNT(*) AS encounter_count
		FROM `tabHealthcare Encounter` e
		WHERE {' AND '.join(conditions)}
		GROUP BY DATE(e.encounter_date)
		ORDER BY posting_date DESC
		""",
		filters,
		as_dict=True,
	)
	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": _("Encounters"), "fieldname": "encounter_count", "fieldtype": "Int", "width": 140},
	]
	return columns, data
