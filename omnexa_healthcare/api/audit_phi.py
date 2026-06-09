# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""PHI access audit logging."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

PHI_DOCTYPES = {
	"Healthcare Patient",
	"Healthcare Encounter",
	"Healthcare Appointment",
	"Healthcare Diagnostic Report",
	"Healthcare Medication Statement",
	"Healthcare Allergy Intolerance",
	"Healthcare Clinical Condition",
}


def log_phi_access(doc, method=None):
	if not frappe.db.get_single_value("Healthcare Settings", "enable_phi_audit_log"):
		return
	if doc.doctype not in PHI_DOCTYPES:
		return
	patient = getattr(doc, "patient", None)
	try:
		frappe.get_doc(
			{
				"doctype": "Healthcare Phi Access Log",
				"user": frappe.session.user,
				"patient": patient,
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"action": "Write" if method in ("on_update", "after_insert") else "Read",
				"accessed_on": now_datetime(),
				"branch": getattr(doc, "branch", None),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "PHI audit log failed")
