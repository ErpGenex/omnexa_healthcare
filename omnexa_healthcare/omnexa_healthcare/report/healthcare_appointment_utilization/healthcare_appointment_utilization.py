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
		conditions.append("DATE(appointment_date) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("DATE(appointment_date) <= %(to_date)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			DATE(appointment_date) AS posting_date,
			status,
			COUNT(name) AS appointments
		FROM `tabHealthcare Appointment`
		WHERE {' AND '.join(conditions)}
		GROUP BY DATE(appointment_date), status
		ORDER BY posting_date DESC
		""",
		filters,
		as_dict=True,
	)
	columns = _columns()
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart


def _columns():
	return [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Appointments"), "fieldname": "appointments", "fieldtype": "Int", "width": 120},
	]
