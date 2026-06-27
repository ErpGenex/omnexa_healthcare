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
	predicted_name = f"HMD-{device_code}"
	if frappe.db.exists("Healthcare Medical Device", predicted_name):
		return {"device": predicted_name, "status": "existing", "fhir_type": "Device"}
	existing = frappe.db.get_value(
		"Healthcare Medical Device",
		{"device_code": device_code, "company": company},
		"name",
	)
	if existing:
		return {"device": existing, "status": "existing", "fhir_type": "Device"}
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


DEVICE_TYPES = [
	"Vital Signs Monitor",
	"Infusion Pump",
	"Ventilator",
	"Defibrillator",
	"Pulse Oximeter",
	"ECG",
	"Lab Analyzer",
	"Imaging Modality",
	"Wearable RPM",
	"Other",
]

PROTOCOLS = ["HL7_ORU", "FHIR_Observation", "ASTM", "DICOM", "MQTT", "REST_API"]

DEPARTMENT_DEVICE_MAP = [
	{"department_ar": "الطوارئ", "department_en": "Emergency", "device_types": ["Vital Signs Monitor", "Defibrillator", "Ventilator", "ECG"]},
	{"department_ar": "ICU / NICU", "department_en": "ICU / NICU", "device_types": ["Vital Signs Monitor", "Ventilator", "Infusion Pump", "Pulse Oximeter"]},
	{"department_ar": "التمريض", "department_en": "Nursing", "device_types": ["Vital Signs Monitor", "Pulse Oximeter", "Wearable RPM"]},
	{"department_ar": "المختبر", "department_en": "Laboratory", "device_types": ["Lab Analyzer"], "protocols": ["HL7_ORU", "ASTM"]},
	{"department_ar": "الأشعة", "department_en": "Radiology", "device_types": ["Imaging Modality"], "protocols": ["DICOM"]},
	{"department_ar": "الصيدلية", "department_en": "Pharmacy", "device_types": ["Infusion Pump"], "protocols": ["REST_API"]},
	{"department_ar": "غرف العمليات", "department_en": "Operating Theatre", "device_types": ["Vital Signs Monitor", "Ventilator", "Infusion Pump", "ECG"]},
	{"department_ar": "غسيل الكلى", "department_en": "Dialysis", "device_types": ["Infusion Pump", "Vital Signs Monitor"]},
	{"department_ar": "الولادة", "department_en": "L&D", "device_types": ["Vital Signs Monitor", "Pulse Oximeter", "ECG"]},
	{"department_ar": "بنك الدم", "department_en": "Blood Bank", "device_types": ["Lab Analyzer"], "protocols": ["ASTM", "HL7_ORU"]},
	{"department_ar": "العيادات الخارجية", "department_en": "Outpatient", "device_types": ["Vital Signs Monitor", "ECG", "Pulse Oximeter"]},
	{"department_ar": "المراقبة عن بُعد", "department_en": "RPM / Telehealth", "device_types": ["Wearable RPM"], "protocols": ["MQTT", "FHIR_Observation", "REST_API"]},
]


@frappe.whitelist()
def get_device_admin_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	devices = list_integrated_devices(company, branch)
	by_type: dict[str, int] = {}
	by_protocol: dict[str, int] = {}
	for d in devices:
		by_type[d.get("device_type") or "Other"] = by_type.get(d.get("device_type") or "Other", 0) + 1
		by_protocol[d.get("integration_protocol") or "REST_API"] = by_protocol.get(d.get("integration_protocol") or "REST_API", 0) + 1
	return {
		"device_types": DEVICE_TYPES,
		"protocols": PROTOCOLS,
		"department_map": DEPARTMENT_DEVICE_MAP,
		"devices": devices,
		"active_count": len(devices),
		"by_type": [{"type": k, "count": v} for k, v in by_type.items()],
		"by_protocol": [{"protocol": k, "count": v} for k, v in by_protocol.items()],
	}


@frappe.whitelist()
def seed_demo_medical_devices(company: str | None = None, branch: str | None = None) -> dict:
	frappe.only_for("System Manager")
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	demo = [
		("ER-VSM-01", "ER Vitals Monitor 1", "Vital Signs Monitor", "Philips", "HL7_ORU"),
		("ICU-VENT-01", "ICU Ventilator 1", "Ventilator", "Hamilton", "HL7_ORU"),
		("LAB-ANZ-01", "Chemistry Analyzer", "Lab Analyzer", "Roche", "ASTM"),
		("RAD-CT-01", "CT Scanner", "Imaging Modality", "Siemens", "DICOM"),
		("PHARM-PUMP-01", "Infusion Pump Ward", "Infusion Pump", "B Braun", "REST_API"),
		("RPM-WATCH-01", "Patient RPM Wearable", "Wearable RPM", "Omron", "MQTT"),
	]
	created = []
	for code, name, dtype, mfr, proto in demo:
		out = register_medical_device(code, name, dtype, mfr, None, branch, company)
		if out.get("device"):
			frappe.db.set_value("Healthcare Medical Device", out["device"], "integration_protocol", proto, update_modified=False)
		created.append(out)
	frappe.db.commit()
	return {"ok": True, "created": created}

