# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Appointment SMS/email reminders — daily scheduler hook."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_to_date, getdate, now_datetime, today


def send_appointment_reminders():
	settings = frappe.get_cached_doc("Healthcare Settings")
	if not settings.get("send_appointment_reminders"):
		return
	hours = int(settings.get("reminder_hours_before") or 24)
	window_start = add_to_date(now_datetime(), hours=hours - 1)
	window_end = add_to_date(now_datetime(), hours=hours + 1)
	appointments = frappe.get_all(
		"Healthcare Appointment",
		filters={
			"status": "Scheduled",
			"appointment_date": ["between", [window_start, window_end]],
		},
		fields=["name", "patient", "patient_display", "appointment_date", "practitioner", "branch"],
	)
	for row in appointments:
		_send_reminder(row)


def _send_reminder(appt: dict):
	settings = frappe.get_cached_doc("Healthcare Settings")
	try:
		if settings.get("enable_sms_reminders") or settings.get("enable_whatsapp_reminders"):
			from omnexa_healthcare.api.patient_notifications import send_appointment_confirmation

			send_appointment_confirmation(appt.name, channels="sms,whatsapp")
		email = _patient_email(appt.patient)
		if email:
			frappe.sendmail(
				recipients=[email],
				subject=_("Appointment reminder — {0}").format(appt.name),
				message=_("Dear {0}, your appointment is scheduled on {1} with {2}.").format(
					appt.patient_display or appt.patient,
					appt.appointment_date,
					appt.practitioner or _("your care team"),
				),
				now=True,
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Healthcare appointment reminder failed")


def _patient_email(patient: str) -> str | None:
	rows = frappe.get_all(
		"Healthcare Patient Telecom",
		filters={"parent": patient, "system": "email"},
		pluck="value",
		limit=1,
	)
	return rows[0] if rows else None
