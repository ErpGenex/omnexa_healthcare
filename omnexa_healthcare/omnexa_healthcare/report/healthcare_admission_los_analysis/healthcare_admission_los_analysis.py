import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from frappe.utils import flt
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["company = %(company)s"]
	if filters.get("branch"):
		conditions.append("branch = %(branch)s")
	if filters.get("from_date"):
		conditions.append("DATE(admission_datetime) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("DATE(admission_datetime) <= %(to_date)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("branch in %(allowed_branches)s")

	rows = frappe.db.sql(
		f"""
		SELECT
			name AS admission,
			branch,
			admission_class,
			status,
			admission_datetime,
			discharge_datetime,
			TIMESTAMPDIFF(HOUR, admission_datetime, IFNULL(discharge_datetime, NOW())) AS los_hours
		FROM `tabHealthcare Admission`
		WHERE {' AND '.join(conditions)}
		ORDER BY admission_datetime DESC
		""",
		filters,
		as_dict=True,
	)
	for row in rows:
		row.los_days = flt((row.los_hours or 0) / 24.0, 2)
	columns = _columns()
	chart = auto_chart_for_columns(rows, columns)
	return columns, rows, None, chart


def _columns():
	return [
		{"label": _("Admission"), "fieldname": "admission", "fieldtype": "Link", "options": "Healthcare Admission", "width": 150},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": _("Class"), "fieldname": "admission_class", "fieldtype": "Data", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Admission Datetime"), "fieldname": "admission_datetime", "fieldtype": "Datetime", "width": 160},
		{"label": _("Discharge Datetime"), "fieldname": "discharge_datetime", "fieldtype": "Datetime", "width": 160},
		{"label": _("LOS (Hours)"), "fieldname": "los_hours", "fieldtype": "Float", "width": 110},
		{"label": _("LOS (Days)"), "fieldname": "los_days", "fieldtype": "Float", "width": 110},
	]
