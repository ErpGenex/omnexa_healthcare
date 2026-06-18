# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Smoke-test healthcare portal APIs (demo hub scope)."""

from __future__ import annotations

import frappe

PORTAL_CALLS: list[tuple[str, str, dict]] = [
	("demo_hub", "omnexa_healthcare.api.healthcare_role_demo.get_healthcare_demo_credentials", {}),
	("demo_hub", "omnexa_healthcare.api.portal_catalog.get_grouped_portal_catalog", {}),
	("reception", "omnexa_healthcare.api.journey_desk.get_reception_kpis", {"company": "MH", "branch": "MH-HO"}),
	("reception", "omnexa_healthcare.api.journey_desk.get_reception_today_appointments", {"company": "MH", "branch": "MH-HO"}),
	("reception", "omnexa_healthcare.api.journey_desk.get_reception_clinics", {"company": "MH", "branch": "MH-HO"}),
	("cashier", "omnexa_healthcare.api.journey_desk.get_cashier_queue", {"company": "MH", "branch": "MH-HO"}),
	("queue", "omnexa_healthcare.api.queue.api_get_patient_queue", {"branch": "MH-HO"}),
	("appointments", "omnexa_healthcare.api.specialty_desks.get_appointments_directory", {"company": "MH", "branch": "MH-HO"}),
	("patients", "omnexa_healthcare.api.specialty_desks.get_patients_directory", {"company": "MH", "branch": "MH-HO"}),
	("pharmacy", "omnexa_healthcare.api.journey_role_desks.get_pharmacy_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("pharmacy", "omnexa_healthcare.api.pharmacy_desk.get_pharmacy_purchases_summary", {"company": "MH", "branch": "MH-HO"}),
	("lab", "omnexa_healthcare.api.lab_desk.get_lab_desk_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("radiology", "omnexa_healthcare.api.radiology_desk.get_radiology_desk_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("er", "omnexa_healthcare.api.er.api_get_er_board", {"branch": "MH-HO"}),
	("icu", "omnexa_healthcare.api.critical_care.api_get_critical_care_board", {"branch": "MH-HO"}),
	("beds", "omnexa_healthcare.api.specialty_desks.get_bed_board", {"branch": "MH-HO"}),
	("ot", "omnexa_healthcare.api.specialty_desks.get_ot_board", {"company": "MH", "branch": "MH-HO"}),
	("dialysis", "omnexa_healthcare.api.specialty_desks.get_dialysis_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("ld", "omnexa_healthcare.api.specialty_desks.get_ld_board_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("optometry", "omnexa_healthcare.api.specialty_desks.get_optometry_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("dental", "omnexa_healthcare.api.dental_desk.get_dental_desk_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("rehab", "omnexa_healthcare.api.specialty_desks.get_rehab_orders", {"company": "MH", "branch": "MH-HO"}),
	("diet", "omnexa_healthcare.api.specialty_desks.get_nutrition_orders", {"company": "MH", "branch": "MH-HO"}),
	("blood", "omnexa_healthcare.api.specialty_desks.get_blood_bank_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("morgue", "omnexa_healthcare.api.specialty_desks.get_morgue_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("finance", "omnexa_healthcare.api.journey_role_desks.get_cfo_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("executive", "omnexa_healthcare.enterprise_assessment.get_enterprise_assessment", {}),
	("device", "omnexa_healthcare.api.device_integration.get_device_admin_dashboard", {"company": "MH", "branch": "MH-HO"}),
	("roster", "omnexa_healthcare.api.scheduling.api_get_practitioner_roster", {"branch": "MH-HO", "roster_date": frappe.utils.today()}),
]


@frappe.whitelist()
def run_portal_api_smoke_test(company: str = "MH", branch: str = "MH-HO") -> dict:
	"""Call portal load APIs and return pass/fail report."""
	results: list[dict] = []
	passed = 0
	for portal, method, kwargs in PORTAL_CALLS:
		kwargs = dict(kwargs)
		if kwargs.get("company") == "MH":
			kwargs["company"] = company
		if kwargs.get("branch") == "MH-HO":
			kwargs["branch"] = branch
		try:
			frappe.get_attr(method)(**kwargs)
			results.append({"portal": portal, "method": method, "ok": True})
			passed += 1
		except Exception as exc:
			results.append({"portal": portal, "method": method, "ok": False, "error": str(exc)[:500]})
	return {"passed": passed, "total": len(PORTAL_CALLS), "results": results}
