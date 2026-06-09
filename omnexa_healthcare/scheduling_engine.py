# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Practitioner scheduling engine — multi-branch slot booking."""

from __future__ import annotations

from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime, getdate


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def practitioner_assigned(practitioner: str, branch: str, specialty: str | None = None) -> bool:
	doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	for row in doc.branch_assignments or []:
		if not row.is_active or row.branch != branch:
			continue
		if specialty and row.specialty != specialty:
			continue
		return True
	return False


def get_practitioner_branches(practitioner: str) -> list[dict]:
	doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	rows = []
	for row in doc.branch_assignments or []:
		if not row.is_active:
			continue
		rows.append(
			{
				"branch": row.branch,
				"facility_profile": row.facility_profile,
				"service_unit": row.service_unit,
				"specialty": row.specialty,
				"consultation_fee": flt(row.consultation_fee),
			}
		)
	return rows


def _as_time(value):
	if value is None:
		return None
	if hasattr(value, "hour"):
		return value
	# Frappe Time fields may arrive as datetime.timedelta
	if hasattr(value, "total_seconds"):
		from datetime import time as dt_time

		seconds = int(value.total_seconds())
		h, rem = divmod(seconds, 3600)
		m, s = divmod(rem, 60)
		return dt_time(h, m, s)
	return value


def get_available_slots(
	practitioner: str,
	branch: str,
	date: str,
	*,
	specialty: str | None = None,
) -> list[dict]:
	"""Return open appointment slots for a practitioner at a branch on a date."""
	if not practitioner_assigned(practitioner, branch, specialty):
		return []

	doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	day_name = WEEKDAYS[getdate(date).weekday()]
	duration = cint(frappe.db.get_single_value("Healthcare Settings", "default_appointment_duration_mins") or 15)

	schedule_lines = [
		row
		for row in doc.schedule or []
		if row.branch == branch and row.day_of_week == day_name and (not specialty or not row.specialty or row.specialty == specialty)
	]
	if not schedule_lines:
		return []

	booked = _booked_intervals(practitioner, date)
	slots: list[dict] = []
	for line in schedule_lines:
		slot_mins = cint(line.slot_duration_mins) or duration
		from_t = _as_time(line.from_time)
		to_t = _as_time(line.to_time)
		cursor = datetime.combine(getdate(date), from_t)
		end = datetime.combine(getdate(date), to_t)
		while cursor + timedelta(minutes=slot_mins) <= end:
			slot_end = cursor + timedelta(minutes=slot_mins)
			if not _overlaps_booked(cursor, slot_end, booked):
				fee = _resolve_consultation_fee(doc, branch, specialty)
				slots.append(
					{
						"start": str(cursor),
						"end": str(slot_end),
						"branch": branch,
						"specialty": specialty,
						"consultation_fee": fee,
					}
				)
			cursor = slot_end
	return slots


def validate_practitioner_appointment(
	*,
	practitioner: str,
	branch: str,
	specialty: str | None,
	slot_start,
	slot_end,
	exclude_appointment: str | None = None,
) -> None:
	if not practitioner:
		return
	if not practitioner_assigned(practitioner, branch, specialty):
		frappe.throw(_("Practitioner is not assigned to this branch/specialty."), title=_("Scheduling"))

	start_dt = get_datetime(slot_start)
	end_dt = get_datetime(slot_end)
	if not start_dt or not end_dt or end_dt <= start_dt:
		frappe.throw(_("Invalid appointment slot times."), title=_("Scheduling"))

	overlaps = frappe.db.sql(
		"""
		SELECT name, branch, appointment_date, slot_end
		FROM `tabHealthcare Appointment`
		WHERE practitioner = %s
			AND status NOT IN ('Cancelled')
			AND docstatus < 2
			AND name != %s
			AND appointment_date < %s
			AND COALESCE(slot_end, appointment_date) > %s
		""",
		(practitioner, exclude_appointment or "", end_dt, start_dt),
		as_dict=True,
	)
	if overlaps:
		row = overlaps[0]
		frappe.throw(
			_("Practitioner already has appointment {0} at branch {1} overlapping this slot.").format(
				row.name, row.branch
			),
			title=_("Scheduling"),
		)


def _booked_intervals(practitioner: str, date: str) -> list[tuple[datetime, datetime]]:
	rows = frappe.get_all(
		"Healthcare Appointment",
		filters={
			"practitioner": practitioner,
			"appointment_date": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
			"status": ["not in", ["Cancelled"]],
			"docstatus": ["<", 2],
		},
		fields=["appointment_date", "slot_end"],
		limit_page_length=500,
	)
	out = []
	for row in rows:
		start = get_datetime(row.appointment_date)
		end = get_datetime(row.slot_end or add_to_date(start, minutes=15))
		out.append((start, end))
	return out


def _overlaps_booked(start: datetime, end: datetime, booked: list[tuple[datetime, datetime]]) -> bool:
	for b_start, b_end in booked:
		if start < b_end and end > b_start:
			return True
	return False


def _resolve_consultation_fee(practitioner_doc, branch: str, specialty: str | None) -> float:
	for row in practitioner_doc.branch_assignments or []:
		if row.branch == branch and row.is_active:
			if specialty and row.specialty == specialty and flt(row.consultation_fee):
				return flt(row.consultation_fee)
			if not specialty and flt(row.consultation_fee):
				return flt(row.consultation_fee)
	return 0.0
