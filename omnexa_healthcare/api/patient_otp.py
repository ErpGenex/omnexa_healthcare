# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Patient OTP verification for portal and mobile."""

from __future__ import annotations

import random
import re

import frappe
from frappe import _
from frappe.utils import now_datetime

OTP_CACHE_PREFIX = "healthcare_patient_otp:"
OTP_TTL_MINUTES = 10


def _normalize_mobile(mobile: str) -> str:
	digits = re.sub(r"\D", "", mobile or "")
	if not digits:
		frappe.throw(_("Mobile number is required."), title=_("OTP"))
	return digits[-12:]


def _otp_enabled() -> bool:
	return bool(frappe.db.get_single_value("Healthcare Settings", "enable_patient_otp"))


@frappe.whitelist(allow_guest=True)
def send_patient_otp(mobile: str, patient: str | None = None) -> dict:
	"""Send OTP to patient mobile (SMS webhook when configured)."""
	if not _otp_enabled():
		frappe.throw(_("Patient OTP is disabled in Healthcare Settings."), title=_("OTP"))
	mobile_key = _normalize_mobile(mobile)
	if patient and not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient not found."), title=_("OTP"))
	otp = f"{random.randint(100000, 999999)}"
	cache_key = f"{OTP_CACHE_PREFIX}{mobile_key}"
	frappe.cache().set_value(cache_key, {"otp": otp, "patient": patient, "sent_at": now_datetime()}, expires_in_sec=OTP_TTL_MINUTES * 60)
	webhook = frappe.db.get_single_value("Healthcare Settings", "otp_sms_webhook_url")
	if webhook:
		try:
			import requests

			requests.post(webhook, json={"mobile": mobile_key, "otp": otp, "patient": patient}, timeout=8)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Healthcare OTP webhook failed")
	return {"ok": True, "mobile": mobile_key, "expires_in_minutes": OTP_TTL_MINUTES, "demo_otp": otp if frappe.conf.developer_mode else None}


@frappe.whitelist(allow_guest=True)
def verify_patient_otp(mobile: str, otp: str, patient: str | None = None) -> dict:
	"""Verify OTP and return session token for portal."""
	mobile_key = _normalize_mobile(mobile)
	cache_key = f"{OTP_CACHE_PREFIX}{mobile_key}"
	payload = frappe.cache().get_value(cache_key)
	if not payload or str(payload.get("otp")) != str(otp).strip():
		frappe.throw(_("Invalid or expired OTP."), title=_("OTP"))
	if patient and payload.get("patient") and payload["patient"] != patient:
		frappe.throw(_("OTP does not match patient."), title=_("OTP"))
	frappe.cache().delete_value(cache_key)
	token = frappe.generate_hash(length=32)
	frappe.cache().set_value(
		f"healthcare_patient_session:{token}",
		{"mobile": mobile_key, "patient": patient or payload.get("patient"), "verified_at": now_datetime()},
		expires_in_sec=86400,
	)
	return {"ok": True, "session_token": token, "patient": patient or payload.get("patient")}
