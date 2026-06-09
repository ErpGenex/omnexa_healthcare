# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Mobile API — device tokens, session config, PWA endpoints."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def register_device_token(device_id: str, platform: str, push_token: str | None = None) -> dict:
	if not (device_id and platform):
		frappe.throw(_("device_id and platform are required"))
	user = frappe.session.user
	existing = frappe.db.get_value(
		"Healthcare Mobile Device Token",
		{"user": user, "device_id": device_id},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Healthcare Mobile Device Token", existing)
		doc.platform = platform
		doc.push_token = push_token
		doc.is_active = 1
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Mobile Device Token",
				"user": user,
				"device_id": device_id,
				"platform": platform,
				"push_token": push_token,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
	return {"name": doc.name, "registered": True}


@frappe.whitelist()
def get_mobile_config() -> dict:
	return {
		"pwa_manifest": "/assets/omnexa_healthcare/pwa/manifest.json",
		"service_worker": "/assets/omnexa_healthcare/pwa/sw.js",
		"rtl_css": "/assets/omnexa_healthcare/css/healthcare-rtl.css",
		"api_version": "global-leader-1",
		"offline_cache": True,
		"push_enabled": True,
	}


@frappe.whitelist()
def mobile_patient_home(patient: str) -> dict:
	from omnexa_healthcare.api.portal import patient_mobile_home

	return patient_mobile_home(patient)


@frappe.whitelist()
def mobile_physician_home() -> dict:
	from omnexa_healthcare.api.physician_app import api_physician_home

	return api_physician_home()
