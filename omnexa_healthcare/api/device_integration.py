# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Medical device integration — vitals monitors, RPM, bedside equipment via API."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


@frappe.whitelist()
def register_medical_device(
	device_code: str,
	device_name: str,
	device_type: str = "Vital Signs Monitor",
	manufacturer: str | None = None,
	model: str | None = None,
	branch: str | None = None,
	company: str | None = None,
) -> dict:
	"""Register a medical device for integration (HL7/FHIR Device mapping)."""
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	if frappe.db.exists("Healthcare Medical Device", {"device_code": device_code, "company": company}):
		return {"device": frappe.db.get_value("Healthcare Medical Device", {"device_code": device_code, "company": company}, "name"), "status": "existing"}
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Medical Device",
			"device_code": device_code,
			"device_name": device_name,
			"device_type": device_type,
			"manufacturer": manufacturer,
			"model_number": model,
			"company": company,
			"branch": branch,
			"status": "Active",
			"integration_protocol": "FHIR_Observation",
		}
	)
	doc.flags.ignore_branch_access = True
	doc.insert(ignore_permissions=True)
	return {"device": doc.name, "status": "created", "fhir_type": "Device"}


@frappe.whitelist()
def ingest_device_vitals(
	patient: str,
	device_code: str,
	readings: str | dict,
	company: str | None = None,
	branch: str | None = None,
) -> dict:
	"""Ingest vitals from bedside monitor / wearable — creates Healthcare Observation rows."""
	data = frappe.parse_json(readings) if isinstance(readings, str) else readings or {}
	if not patient or not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient is required."), title=_("Device"))
	company = company or frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = branch or frappe.db.get_value("Healthcare Patient", patient, "branch")
	device = frappe.db.get_value("Healthcare Medical Device", {"device_code": device_code, "company": company}, "name")
	created = []
	profile_map = {
		"bp_systolic": "blood_pressure",
		"bp_diastolic": "blood_pressure",
		"heart_rate": "heart_rate",
		"temperature": "body_temperature",
		"weight": "body_weight",
		"spo2": "oxygen_saturation",
	}
	bp_sys = flt(data.get("bp_systolic")) if data.get("bp_systolic") not in (None, "") else None
	bp_dia = flt(data.get("bp_diastolic")) if data.get("bp_diastolic") not in (None, "") else None
	if bp_sys is not None or bp_dia is not None:
		obs = frappe.get_doc(
			{
				"doctype": "Healthcare Observation",
				"patient": patient,
				"company": company,
				"branch": branch,
				"observation_profile": "blood_pressure",
				"value_primary": bp_sys or 0,
				"value_secondary": bp_dia or 0,
				"effective_datetime": now_datetime(),
				"status": "final",
				"notes": _("Device {0}").format(device_code),
			}
		)
		obs.flags.ignore_branch_access = True
		obs.insert(ignore_permissions=True)
		created.append(obs.name)
	for key, val in data.items():
		if key in ("bp_systolic", "bp_diastolic") or val is None or val == "":
			continue
		profile = profile_map.get(key, key)
		obs = frappe.get_doc(
			{
				"doctype": "Healthcare Observation",
				"patient": patient,
				"company": company,
				"branch": branch,
				"observation_profile": profile,
				"value_primary": flt(val),
				"effective_datetime": now_datetime(),
				"status": "final",
				"notes": _("Device {0}").format(device_code),
			}
		)
		obs.flags.ignore_branch_access = True
		obs.insert(ignore_permissions=True)
		created.append(obs.name)
	return {"observations": created, "count": len(created), "device": device}


@frappe.whitelist()
def list_integrated_devices(company: str | None = None, branch: str | None = None) -> list[dict]:
	company = company or frappe.defaults.get_user_default("Company")
	filters: dict = {"company": company, "status": "Active"}
	if branch:
		filters["branch"] = branch
	if not frappe.db.exists("DocType", "Healthcare Medical Device"):
		return []
	return frappe.get_all(
		"Healthcare Medical Device",
		filters=filters,
		fields=["name", "device_code", "device_name", "device_type", "manufacturer", "integration_protocol"],
		limit=100,
	)
