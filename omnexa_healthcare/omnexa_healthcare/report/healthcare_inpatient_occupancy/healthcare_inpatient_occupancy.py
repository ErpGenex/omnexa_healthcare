import frappe
from frappe import _
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

	data = frappe.db.sql(
		f"""
		SELECT
			status AS admission_status,
			COUNT(name) AS admissions
		FROM `tabHealthcare Admission`
		WHERE {' AND '.join(conditions)}
		GROUP BY status
		ORDER BY admissions DESC
		""",
		filters,
		as_dict=True,
	)
	return _columns(), data


def _columns():
	return [
		{"label": _("Admission Status"), "fieldname": "admission_status", "fieldtype": "Data", "width": 180},
		{"label": _("Admissions"), "fieldname": "admissions", "fieldtype": "Int", "width": 120},
	]
