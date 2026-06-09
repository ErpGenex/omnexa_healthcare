import frappe
from frappe import _
from frappe.utils import flt
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["a.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("a.branch = %(branch)s")
	if filters.get("from_date"):
		conditions.append("DATE(a.appointment_date) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("DATE(a.appointment_date) <= %(to_date)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("a.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			a.practitioner,
			a.specialty,
			a.branch,
			COUNT(*) AS booked_slots,
			SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
			SUM(CASE WHEN a.status IN ('Cancelled', 'No Show') THEN 1 ELSE 0 END) AS lost_slots
		FROM `tabHealthcare Appointment` a
		WHERE {' AND '.join(conditions)}
		GROUP BY a.practitioner, a.specialty, a.branch
		ORDER BY booked_slots DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.utilization_pct = flt(row.completed) / flt(row.booked_slots) * 100 if row.booked_slots else 0
	return _columns(), data


def _columns():
	return [
		{"label": _("Practitioner"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},
		{"label": _("Specialty"), "fieldname": "specialty", "fieldtype": "Link", "options": "Healthcare Specialty", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Booked"), "fieldname": "booked_slots", "fieldtype": "Int", "width": 90},
		{"label": _("Completed"), "fieldname": "completed", "fieldtype": "Int", "width": 100},
		{"label": _("Lost"), "fieldname": "lost_slots", "fieldtype": "Int", "width": 80},
		{"label": _("Utilization %"), "fieldname": "utilization_pct", "fieldtype": "Percent", "width": 120},
	]
