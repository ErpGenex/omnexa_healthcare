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
			COUNT(*) AS total_appointments,
			SUM(
				CASE
					WHEN a.status = 'No Show' THEN 1
					WHEN a.status = 'Scheduled'
						AND DATE(a.appointment_date) < CURDATE()
						AND IFNULL(a.encounter, '') = '' THEN 1
					ELSE 0
				END
			) AS no_shows,
			SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed
		FROM `tabHealthcare Appointment` a
		WHERE {' AND '.join(conditions)}
		GROUP BY a.practitioner, a.specialty, a.branch
		ORDER BY no_shows DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.no_show_rate = flt(row.no_shows) / flt(row.total_appointments) * 100 if row.total_appointments else 0
	return _columns(), data


def _columns():
	return [
		{"label": _("Practitioner"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},
		{"label": _("Specialty"), "fieldname": "specialty", "fieldtype": "Link", "options": "Healthcare Specialty", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Total"), "fieldname": "total_appointments", "fieldtype": "Int", "width": 90},
		{"label": _("No Shows"), "fieldname": "no_shows", "fieldtype": "Int", "width": 90},
		{"label": _("Completed"), "fieldname": "completed", "fieldtype": "Int", "width": 100},
		{"label": _("No Show %"), "fieldname": "no_show_rate", "fieldtype": "Percent", "width": 110},
	]
