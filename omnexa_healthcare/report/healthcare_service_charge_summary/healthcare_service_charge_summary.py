import frappe
from frappe import _
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
			h.posting_date,
			h.branch,
			h.status,
			COUNT(DISTINCT h.name) AS service_charge_docs,
			COALESCE(SUM(i.amount), 0) AS charge_amount
		FROM `tabHealthcare Service Charge` h
		LEFT JOIN `tabHealthcare Service Charge Line` i ON i.parent = h.name
		WHERE {' AND '.join(conditions)}
		GROUP BY h.posting_date, h.branch, h.status
		ORDER BY h.posting_date DESC, h.branch ASC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.charge_amount = flt(row.charge_amount)
	return _columns(), data


def _columns():
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Service Charge Docs"), "fieldname": "service_charge_docs", "fieldtype": "Int", "width": 140},
		{"label": _("Charge Amount"), "fieldname": "charge_amount", "fieldtype": "Currency", "width": 130},
	]
