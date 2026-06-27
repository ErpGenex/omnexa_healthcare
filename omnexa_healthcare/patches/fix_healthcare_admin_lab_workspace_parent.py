# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Fix Healthcare Admin Lab workspace: set parent_page to Healthcare for sidebar nesting."""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("Workspace", "Healthcare Admin Lab"):
		return

	ws = frappe.get_doc("Workspace", "Healthcare Admin Lab")
	changed = False

	# Set parent_page to Healthcare for sidebar nesting
	if (ws.parent_page or "").strip() != "Healthcare":
		ws.parent_page = "Healthcare"
		changed = True

	# Ensure icon is set
	if not ws.icon:
		ws.icon = "es-line-flask"
		changed = True

	if changed:
		ws.flags.ignore_permissions = True
		ws.flags.ignore_version = True
		ws.save()
		frappe.clear_cache(doctype="Workspace")
		frappe.msgprint("Healthcare Admin Lab workspace updated: parent_page=Healthcare")
