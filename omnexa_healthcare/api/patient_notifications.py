# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""SMS / WhatsApp appointment confirmations and reminders."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url


@frappe.whitelist()
def send_appointment_confirmation(appointment: str, channels: str | None = None) -> dict:
	"""Send booking confirmation via email, SMS, and/or WhatsApp."""
	appt = frappe.get_doc("Healthcare Appointment", appointment)
	settings = frappe.get_cached_doc("Healthcare Settings")
	channels = [c.strip().lower() for c in (channels or "email,sms,whatsapp").split(",") if c.strip()]
	results = {}
	if "email" in channels:
		results["email"] = _send_email(appt)
	if "sms" in channels and settings.get("enable_sms_reminders"):
		results["sms"] = _send_sms(appt, settings)
	if "whatsapp" in channels and settings.get("enable_whatsapp_reminders"):
		results["whatsapp"] = _send_whatsapp(appt, settings)
	return {"appointment": appointment, "channels": results}


def _send_email(appt) -> bool:
	email = _patient_contact(appt.patient, "email")
	if not email:
		return False
	frappe.sendmail(
		recipients=[email],
		subject=_("Appointment confirmed — {0}").format(appt.name),
		message=_("Your appointment on {0} is confirmed. Reference: {1}").format(appt.appointment_date, appt.name),
		now=True,
	)
	return True


def _send_sms(appt, settings) -> bool:
	phone = _patient_contact(appt.patient, "phone") or _patient_contact(appt.patient, "mobile")
	if not phone:
		return False
	msg = _("Appointment confirmed {0} on {1}").format(appt.name, appt.appointment_date)
	return _dispatch_webhook(settings.get("sms_webhook_url"), {"to": phone, "message": msg, "appointment": appt.name})


def _send_whatsapp(appt, settings) -> bool:
	phone = _patient_contact(appt.patient, "mobile") or _patient_contact(appt.patient, "phone")
	if not phone:
		return False
	msg = _("Your healthcare appointment is confirmed for {0}. Ref: {1}").format(appt.appointment_date, appt.name)
	return _dispatch_webhook(settings.get("whatsapp_webhook_url"), {"to": phone, "message": msg, "appointment": appt.name})


def _dispatch_webhook(url: str | None, payload: dict) -> bool:
	if not url:
		frappe.logger("omnexa_healthcare").info(f"Notification (no webhook): {payload}")
		return True
	try:
		import requests

		resp = requests.post(url, json=payload, timeout=10)
		return resp.ok
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Healthcare notification webhook failed")
		return False


def _patient_contact(patient: str, system: str) -> str | None:
	rows = frappe.get_all(
		"Healthcare Patient Telecom",
		filters={"parent": patient, "system": system},
		pluck="value",
		limit=1,
	)
	return rows[0] if rows else None
