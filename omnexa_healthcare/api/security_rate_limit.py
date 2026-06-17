# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""API rate limiting and OAuth scope helpers."""

from __future__ import annotations

import frappe
from frappe import _

RATE_LIMIT_CACHE_PREFIX = "omnexa_api_rate:"


@frappe.whitelist()
def check_api_rate_limit(user: str | None = None, limit: int = 120, window_seconds: int = 60) -> dict:
	"""Simple sliding-window rate limit for whitelisted healthcare APIs."""
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)
	key = f"{RATE_LIMIT_CACHE_PREFIX}{user}"
	count = frappe.cache().get_value(key) or 0
	if count >= int(limit):
		frappe.throw(_("Rate limit exceeded. Try again later."), frappe.RateLimitExceededError)
	frappe.cache().set_value(key, count + 1, expires_in_sec=int(window_seconds))
	return {"ok": True, "remaining": int(limit) - count - 1}


@frappe.whitelist()
def get_oauth_scopes() -> list[dict]:
	return [
		{"scope": "healthcare.read", "description": "Read clinical resources"},
		{"scope": "healthcare.write", "description": "Create/update clinical resources"},
		{"scope": "healthcare.fhir", "description": "FHIR REST access"},
		{"scope": "healthcare.erx", "description": "ePrescription sign and verify"},
		{"scope": "healthcare.phi", "description": "PHI access (MFA required)"},
	]
