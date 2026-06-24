import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["company = %(company)s"]
	if filters.get("branch"):
		conditions.append("branch = %(branch)s")
	if filters.get("from_date"):
		conditions.append("DATE(effective_datetime) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("DATE(effective_datetime) <= %(to_date)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			report_category,
			status,
			COUNT(name) AS reports
		FROM `tabHealthcare Diagnostic Report`
		WHERE {' AND '.join(conditions)}
		GROUP BY report_category, status
		ORDER BY reports DESC
		""",
		filters,
		as_dict=True,
	)
	columns = _columns()
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart


def _columns():
	return [
		{"label": _("Report Category"), "fieldname": "report_category", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
		{"label": _("Reports"), "fieldname": "reports", "fieldtype": "Int", "width": 100},
	]
