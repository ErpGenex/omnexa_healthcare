# -*- coding: utf-8 -*-
"""HIPAA/GDPR-aligned access tokens for telemedicine sessions."""

from __future__ import annotations

import time

import frappe
import jwt


def _signing_secret(purpose: str = "telemedicine") -> str:
	site_secret = (
		frappe.get_site_config().get("encryption_key")
		or frappe.get_site_config().get("secret_key")
		or frappe.local.conf.get("db_name")
	)
	return f"{site_secret}:{purpose}"


def generate_session_access_token(
	session_id: str,
	user: str | None = None,
	role: str = "participant",
	ttl_seconds: int = 3600,
) -> str:
	user = user or frappe.session.user
	now = int(time.time())
	payload = {
		"typ": "telemedicine_session",
		"session_id": session_id,
		"user": user,
		"role": role,
		"iat": now,
		"exp": now + ttl_seconds,
	}
	return jwt.encode(payload, _signing_secret("telemedicine"), algorithm="HS256")


def verify_session_access_token(token: str, session_id: str | None = None) -> dict:
	payload = jwt.decode(token, _signing_secret("telemedicine"), algorithms=["HS256"])
	if payload.get("typ") != "telemedicine_session":
		frappe.throw("Invalid telemedicine token type")
	if session_id and payload.get("session_id") != session_id:
		frappe.throw("Token session mismatch")
	return payload


def generate_jitsi_jwt(room_name: str, display_name: str, is_moderator: bool = False) -> str | None:
	from omnexa_healthcare.api.telemedicine_admin import ensure_telemedicine_configuration

	config = ensure_telemedicine_configuration()
	app_id = (config.jitsi_app_id or "").strip()
	secret = (config.jitsi_secret or "").strip()
	domain = (config.jitsi_domain or "meet.jit.si").strip()

	if not app_id or not secret:
		return None

	now = int(time.time())
	payload = {
		"aud": "jitsi",
		"iss": app_id,
		"sub": domain,
		"room": room_name,
		"exp": now + 3600,
		"nbf": now - 10,
		"context": {
			"user": {
				"name": display_name,
				"email": frappe.session.user,
				"moderator": bool(is_moderator),
			}
		},
	}
	return jwt.encode(payload, secret, algorithm="HS256")
