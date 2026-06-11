# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Bed occupancy forecasting for hospital operations."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import add_days, getdate, today


@frappe.whitelist()
def forecast_bed_occupancy(days: int = 7, company: str | None = None, branch: str | None = None) -> dict:
	"""Simple moving-average occupancy forecast."""
	days = max(1, min(int(days or 7), 30))
	filters: dict = {}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	total_beds = frappe.db.count("Healthcare Bed", {**filters, "status": ["!=", ""]})
	occupied = frappe.db.count("Healthcare Bed", {**filters, "status": "Occupied"})
	current_rate = round(occupied / total_beds * 100, 1) if total_beds else 0.0
	admissions_7d = frappe.db.count(
		"Healthcare Admission",
		{**filters, "admission_datetime": [">=", add_days(today(), -7)]},
	)
	discharges_7d = frappe.db.count(
		"Healthcare Admission",
		{**filters, "status": "discharged", "modified": [">=", add_days(today(), -7)]},
	)
	daily_net = (admissions_7d - discharges_7d) / 7.0
	forecast: list[dict] = []
	rate = current_rate
	for i in range(1, days + 1):
		delta = (daily_net / max(total_beds, 1)) * 100 * 0.5
		rate = max(0.0, min(100.0, rate + delta))
		forecast.append({"date": str(add_days(today(), i)), "occupancy_pct": round(rate, 1)})
	return {
		"total_beds": total_beds,
		"occupied_beds": occupied,
		"current_occupancy_pct": current_rate,
		"forecast_days": days,
		"forecast": forecast,
		"method": "7-day admission/discharge moving average",
	}
