# Copyright (c) 2026, ErpGenEx
"""Healthcare Workcenter — primary portal entry (replaces legacy Demo Hub route)."""

from __future__ import annotations

import frappe
from frappe import _

WORKCENTER_PAGE = "healthcare-workcenter"
LEGACY_DEMO_PAGE = "healthcare-demo-hub"
WORKCENTER_ROUTE = f"/app/{WORKCENTER_PAGE}"


def ensure_workcenter_page() -> dict:
	if frappe.db.exists("Page", WORKCENTER_PAGE):
		frappe.db.set_value("Page", WORKCENTER_PAGE, "title", _("Healthcare Workcenter"), update_modified=False)
	else:
		page = frappe.get_doc(
			{
				"doctype": "Page",
				"module": "Omnexa Healthcare",
				"name": WORKCENTER_PAGE,
				"page_name": WORKCENTER_PAGE,
				"title": _("Healthcare Workcenter"),
				"standard": "Yes",
			}
		)
		page.append("roles", {"role": "System Manager"})
		page.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "page": WORKCENTER_PAGE}


def sync_workcenter_page_roles() -> None:
	if not frappe.db.exists("Page", WORKCENTER_PAGE):
		return
	page = frappe.get_doc("Page", WORKCENTER_PAGE)
	existing = {r.role for r in page.roles}
	for role in ("System Manager", "Company Admin", "Healthcare Manager"):
		if role not in existing and frappe.db.exists("Role", role):
			page.append("roles", {"role": role})
	page.flags.ignore_permissions = True
	page.save()
