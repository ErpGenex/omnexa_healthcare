# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.report_print.report_query_filters import (
	get_all_filters,
	policy_version_filters,
	prepare_filters,
	sql_conditions,
)



def execute(filters=None):
	columns = [
		{"label": _("Admission Status"), "fieldname": "admission_status", "fieldtype": "Data", "width": 180},
		{"label": _("Admissions"), "fieldname": "admissions", "fieldtype": "Int", "width": 140},
	]
	filters = prepare_filters(filters)
	conditions, params = sql_conditions(filters, "Healthcare Admission", date_field="creation", company=True, branch=True)
	rows = frappe.db.sql(
		f"""
		SELECT
			IFNULL(a.admission_status, 'unknown') AS admission_status,
			COUNT(*) AS admissions
		FROM `tabHealthcare Admission`
		WHERE {' AND '.join(conditions)}
		GROUP BY a.admission_status
		ORDER BY admissions DESC
		""",
		params,
		as_dict=True,
	)
	return columns, rows
