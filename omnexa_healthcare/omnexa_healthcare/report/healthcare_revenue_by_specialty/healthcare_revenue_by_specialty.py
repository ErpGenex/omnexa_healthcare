import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from frappe.utils import flt
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["h.company = %(company)s", "h.docstatus < 2"]
	if filters.get("branch"):
		conditions.append("h.branch = %(branch)s")
	if filters.get("from_date"):
		conditions.append("h.posting_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("h.posting_date <= %(to_date)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("h.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			COALESCE(a.specialty, po.specialty, e.specialty) AS specialty,
			COALESCE(a.practitioner, e.practitioner) AS practitioner,
			h.branch,
			COUNT(DISTINCT h.name) AS charge_count,
			COALESCE(SUM(l.amount), 0) AS revenue
		FROM `tabHealthcare Service Charge` h
		LEFT JOIN `tabHealthcare Service Charge Line` l ON l.parent = h.name
		LEFT JOIN `tabHealthcare Appointment` a ON a.service_charge = h.name
		LEFT JOIN `tabHealthcare Procedure Order` po ON po.service_charge = h.name
		LEFT JOIN `tabHealthcare Encounter` e ON e.name = a.encounter OR e.name = po.encounter
		WHERE {' AND '.join(conditions)}
		GROUP BY specialty, practitioner, h.branch
		ORDER BY revenue DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.revenue = flt(row.revenue)
	columns = _columns()
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart


def _columns():
	return [
		{"label": _("Specialty"), "fieldname": "specialty", "fieldtype": "Link", "options": "Healthcare Specialty", "width": 160},
		{"label": _("Practitioner"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Charges"), "fieldname": "charge_count", "fieldtype": "Int", "width": 90},
		{"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
	]
