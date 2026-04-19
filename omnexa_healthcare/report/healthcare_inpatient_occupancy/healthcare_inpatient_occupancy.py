# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	data = frappe.db.sql(
		"""
		SELECT
			IFNULL(a.admission_status, 'unknown') AS admission_status,
			COUNT(*) AS admissions
		FROM `tabHealthcare Admission` a
		WHERE a.company = %(company)s
		GROUP BY a.admission_status
		ORDER BY admissions DESC
		""",
		filters,
		as_dict=True,
	)
	columns = [
		{"label": _("Admission Status"), "fieldname": "admission_status", "fieldtype": "Data", "width": 180},
		{"label": _("Admissions"), "fieldname": "admissions", "fieldtype": "Int", "width": 140},
	]
	return columns, data
