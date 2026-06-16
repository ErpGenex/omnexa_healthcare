# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.gap_closure_wave6_defs import GAP_CLOSURE_WAVE6_DOCTYPES

_FM_DOCTYPES = [
	"Healthcare Family Unit",
	"Healthcare Family History",
	"Healthcare Preventive Care Plan",
	"Healthcare Family Risk Score",
]


def _ensure_fm_physician_role() -> None:
	if frappe.db.exists("Role", "FM Physician"):
		return
	frappe.get_doc({"doctype": "Role", "role_name": "FM Physician", "desk_access": 1}).insert(
		ignore_permissions=True
	)
	for dt in _FM_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			continue
		if frappe.db.exists("Custom DocPerm", {"parent": dt, "role": "FM Physician"}):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": dt,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "FM Physician",
				"read": 1,
				"write": 1,
				"create": 1,
				"export": 1,
				"report": 1,
			}
		).insert(ignore_permissions=True)


def execute():
	settings = frappe.get_doc("Healthcare Settings")
	if hasattr(settings, "enable_family_medicine"):
		settings.enable_family_medicine = 1
	settings.save(ignore_permissions=True)

	_ensure_fm_physician_role()

	for spec in GAP_CLOSURE_WAVE6_DOCTYPES:
		if spec.get("istable"):
			continue
		if not frappe.db.exists("DocType", spec["name"]):
			frappe.logger("omnexa_healthcare").warning("seed_gap_closure_wave6: missing %s", spec["name"])

	try:
		from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace

		sync_healthcare_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_gap_closure_wave6 workspace sync")

	frappe.logger("omnexa_healthcare").info("seed_gap_closure_wave6: family medicine + FM Physician role")
