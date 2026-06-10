# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Dental Center of Excellence — chart API (FDI + Universal numbering)."""

from __future__ import annotations

import frappe
from frappe import _


FDI_ADULT = [11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28, 31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48]
UNIVERSAL_ADULT = list(range(1, 33))


@frappe.whitelist()
def get_tooth_numbering_map(system: str = "FDI") -> dict:
	system = (system or "FDI").upper()
	if system == "UNIVERSAL":
		return {"system": "Universal", "teeth": UNIVERSAL_ADULT}
	return {"system": "FDI", "teeth": FDI_ADULT}


@frappe.whitelist()
def get_patient_dental_chart(patient: str, numbering_system: str = "FDI") -> dict:
	if not frappe.db.exists("Healthcare Patient", patient):
		frappe.throw(_("Patient does not exist."), title=_("Patient"))
	entries = frappe.get_all(
		"Healthcare Dental Chart Entry",
		filters={"patient": patient, "tooth_numbering_system": numbering_system},
		fields=["name", "tooth_id", "surface", "condition", "treatment_plan", "status", "encounter", "modified"],
		order_by="tooth_id",
	)
	return {
		"patient": patient,
		"numbering_system": numbering_system,
		"entries": entries,
		"tooth_map": get_tooth_numbering_map(numbering_system),
	}


@frappe.whitelist()
def upsert_dental_chart_entry(
	patient: str,
	tooth_id: str,
	company: str,
	condition: str = "healthy",
	numbering_system: str = "FDI",
	surface: str | None = None,
	treatment_plan: str | None = None,
	status: str = "planned",
	encounter: str | None = None,
	practitioner: str | None = None,
	branch: str | None = None,
) -> dict:
	existing = frappe.db.get_value(
		"Healthcare Dental Chart Entry",
		{"patient": patient, "tooth_id": tooth_id, "tooth_numbering_system": numbering_system, "surface": surface or ""},
		"name",
	)
	payload = {
		"patient": patient,
		"tooth_id": tooth_id,
		"tooth_numbering_system": numbering_system,
		"condition": condition,
		"status": status,
		"company": company,
		"surface": surface,
		"treatment_plan": treatment_plan,
		"encounter": encounter,
		"practitioner": practitioner,
		"branch": branch,
	}
	if existing:
		doc = frappe.get_doc("Healthcare Dental Chart Entry", existing)
		doc.update(payload)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Healthcare Dental Chart Entry", **payload})
		doc.insert(ignore_permissions=True)
	return {"name": doc.name, "tooth_id": tooth_id, "condition": condition, "status": status}
