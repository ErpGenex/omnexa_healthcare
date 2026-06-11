# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Home healthcare visits and lab collection."""

from __future__ import annotations

import frappe
from frappe import _


def _home_health_enabled() -> bool:
	return bool(frappe.db.get_single_value("Healthcare Settings", "enable_home_healthcare"))


@frappe.whitelist()
def request_home_visit(patient: str, visit_type: str, address: str, company: str, branch: str, scheduled_datetime: str | None = None, practitioner: str | None = None, notes: str | None = None) -> dict:
	if not _home_health_enabled():
		frappe.throw(_("Home healthcare is disabled."), title=_("Home Health"))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Home Visit Request",
			"patient": patient,
			"visit_type": visit_type,
			"address": address,
			"scheduled_datetime": scheduled_datetime,
			"practitioner": practitioner,
			"status": "Requested",
			"company": company,
			"branch": branch,
			"notes": notes,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "visit": doc.name, "status": doc.status}


@frappe.whitelist()
def list_home_visits(patient: str | None = None, status: str | None = None) -> list[dict]:
	filters: dict = {}
	if patient:
		filters["patient"] = patient
	if status:
		filters["status"] = status
	return frappe.get_all(
		"Healthcare Home Visit Request",
		filters=filters,
		fields=["name", "patient", "visit_type", "scheduled_datetime", "address", "practitioner", "status"],
		order_by="scheduled_datetime desc",
	)


@frappe.whitelist()
def request_home_lab_collection(patient: str, address: str, company: str, branch: str, service_request: str | None = None, scheduled_datetime: str | None = None) -> dict:
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Home Lab Collection Request",
			"patient": patient,
			"service_request": service_request,
			"address": address,
			"scheduled_datetime": scheduled_datetime,
			"status": "Requested",
			"company": company,
			"branch": branch,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "request": doc.name}
