# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Physician mobile / web app API."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, today

from omnexa_healthcare.api.in_basket import api_get_in_basket


@frappe.whitelist()
def api_physician_home(practitioner: str | None = None) -> dict:
	user = frappe.session.user
	if not practitioner:
		practitioner = frappe.db.get_value("Healthcare Practitioner", {"user": user}, "name")
	appointments = []
	if practitioner:
		appointments = frappe.get_all(
			"Healthcare Appointment",
			filters={"practitioner": practitioner, "appointment_date": getdate(today()), "status": ["not in", ["Cancelled"]]},
			fields=["name", "patient", "appointment_date", "status", "specialty"],
			order_by="appointment_date asc",
			limit=50,
		)
	return {
		"practitioner": practitioner,
		"appointments_today": appointments,
		"in_basket": api_get_in_basket(),
	}
