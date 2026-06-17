# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave9_defs import GAP_CLOSURE_WAVE9_DOCTYPES


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	for field in ("enable_phi_audit_log", "enforce_mfa_for_phi_roles", "enforce_mfa_hard_block", "enable_field_phi_masking"):
		if hasattr(settings, field):
			setattr(settings, field, 1)
	settings.save(ignore_permissions=True)

	for spec in GAP_CLOSURE_WAVE9_DOCTYPES:
		if not frappe.db.exists("DocType", spec["name"]):
			frappe.logger("omnexa_healthcare").warning("seed_gap_closure_wave9: missing %s", spec["name"])

	try:
		from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace

		sync_healthcare_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave9 workspace sync")

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave9: compliance + security hardening")
