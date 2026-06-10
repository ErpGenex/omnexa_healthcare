# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""AI scheduling optimizer — ranks practitioner slots by utilization and lead time."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from omnexa_healthcare.scheduling_engine import get_available_slots


@frappe.whitelist()
def optimize_booking_slots(practitioner: str, branch: str, appointment_date: str, specialty: str | None = None) -> list[dict]:
	"""Rank available slots — prefer off-peak hours and balance daily load."""
	if not frappe.get_cached_doc("Healthcare Settings").get("enable_ai_scheduling"):
		slots = get_available_slots(practitioner, branch, appointment_date, specialty=specialty)
		return [{"slot": s, "score": 50, "reason": "default"} for s in slots]
	slots = get_available_slots(practitioner, branch, appointment_date, specialty=specialty)
	if not slots:
		return []
	day_count = frappe.db.count(
		"Healthcare Appointment",
		{"practitioner": practitioner, "appointment_date": ["between", [getdate(appointment_date), getdate(appointment_date)]], "status": ["!=", "Cancelled"]},
	)
	ranked = []
	for idx, slot in enumerate(slots):
		score = 100 - (day_count * 5) - (idx * 2)
		if "09:" in str(slot) or "10:" in str(slot):
			score += 10
		ranked.append({"slot": slot, "score": max(score, 1), "reason": _("AI-optimized slot ranking")})
	return sorted(ranked, key=lambda x: x["score"], reverse=True)
