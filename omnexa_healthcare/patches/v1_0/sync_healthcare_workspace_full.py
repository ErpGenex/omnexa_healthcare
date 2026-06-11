"""Rebuild Healthcare workspace menu after migrate (full catalog, not legacy fixture)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("Workspace", "Healthcare"):
		return

	from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace_menu

	stats = sync_healthcare_workspace_menu(save=True, rebuild=True)
	frappe.logger("omnexa_healthcare").info(
		"Healthcare workspace synced: %s links, %s sections",
		stats.get("total_links"),
		stats.get("sections"),
	)
