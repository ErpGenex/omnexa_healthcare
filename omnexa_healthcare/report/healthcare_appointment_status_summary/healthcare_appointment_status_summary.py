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
			status,
			department,
			service_unit,
			COUNT(name) AS appointments
		FROM `tabHealthcare Appointment`
		WHERE {' AND '.join(conditions)}
		GROUP BY status, department, service_unit
		ORDER BY appointments DESC
		""",
		filters,
		as_dict=True,
	)
	return _columns(), data


def _columns():
	return [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Healthcare Department", "width": 170},
		{"label": _("Service Unit"), "fieldname": "service_unit", "fieldtype": "Link", "options": "Healthcare Service Unit", "width": 170},
		{"label": _("Appointments"), "fieldname": "appointments", "fieldtype": "Int", "width": 120},
	]
