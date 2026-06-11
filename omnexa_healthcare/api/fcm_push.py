# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""FCM push notification infrastructure (web/mobile token based)."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def register_fcm_token(patient: str, token: str, platform: str = "web") -> dict:
	"""Store FCM device token for patient push notifications."""
	if not patient or not token:
		frappe.throw(_("Patient and token are required."), title=_("FCM"))
	cache_key = f"healthcare_fcm:{patient}:{platform}"
	frappe.cache().set_value(cache_key, {"token": token, "platform": platform}, expires_in_sec=86400 * 90)
	return {"ok": True, "patient": patient, "platform": platform}


@frappe.whitelist()
def send_fcm_push(patient: str, title: str, body: str) -> dict:
	"""Queue FCM push via configured webhook (production gateway)."""
	webhook = frappe.db.get_single_value("Healthcare Settings", "fcm_webhook_url")
	if not webhook:
		frappe.logger("omnexa_healthcare").info(f"FCM stub: {patient} — {title}: {body}")
		return {"ok": True, "queued": False, "mode": "log_only", "title": title}
	try:
		import requests

		requests.post(webhook, json={"patient": patient, "title": title, "body": body}, timeout=8)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Healthcare FCM webhook failed")
	return {"ok": True, "queued": True, "patient": patient}
