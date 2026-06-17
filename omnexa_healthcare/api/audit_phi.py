# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""PHI access audit logging — 26+ DocTypes."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from omnexa_healthcare.gap_closure_wave9_defs import PHI_AUDIT_DOCTYPES

PHI_DOCTYPES = set(PHI_AUDIT_DOCTYPES)


def log_phi_access(doc, method=None):
	if not frappe.db.get_single_value("Healthcare Settings", "enable_phi_audit_log"):
		return
	if doc.doctype not in PHI_DOCTYPES:
		return
	patient = getattr(doc, "patient", None) or getattr(doc, "head_of_family", None)
	action = "Write" if method in ("on_update", "after_insert", "on_submit") else "Read"
	try:
		frappe.get_doc(
			{
				"doctype": "Healthcare Phi Access Log",
				"user": frappe.session.user,
				"patient": patient,
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"action": action,
				"accessed_on": now_datetime(),
				"branch": getattr(doc, "branch", None),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "PHI audit log failed")


def register_phi_doc_events() -> dict:
	"""Return doc_events map for all PHI doctypes."""
	return {dt: {"on_update": "omnexa_healthcare.api.audit_phi.log_phi_access", "after_insert": "omnexa_healthcare.api.audit_phi.log_phi_access"} for dt in PHI_DOCTYPES}
