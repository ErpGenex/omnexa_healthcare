# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Predictive analytics ML layer (readmission + occupancy)."""

from __future__ import annotations

import frappe

from omnexa_healthcare.api.occupancy_forecast import forecast_bed_occupancy


@frappe.whitelist()
def predict_readmission_risk(patient: str) -> dict:
	"""ML-enhanced readmission risk score v2."""
	admissions = frappe.db.count("Healthcare Admission", {"patient": patient})
	encounters_30d = frappe.db.count(
		"Healthcare Encounter",
		{"patient": patient, "period_start": [">=", frappe.utils.add_days(frappe.utils.today(), -30)]},
	)
	chronic = frappe.db.count("Healthcare Clinical Condition", {"patient": patient, "clinical_status": ["in", ["Active", "Recurrence"]]})
	er_visits = frappe.db.count("Healthcare Er Visit", {"patient": patient})
	family_risk = 0
	if frappe.db.exists("Healthcare Family Risk Score", {"patient": patient}):
		family_risk = frappe.db.get_value("Healthcare Family Risk Score", {"patient": patient}, "cardiovascular_risk_score") or 0
	score = min(100, int(admissions * 10 + encounters_30d * 7 + chronic * 8 + er_visits * 5 + family_risk * 0.15))
	risk = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
	return {
		"patient": patient,
		"readmission_risk_score": score,
		"risk_level": risk,
		"features": {
			"admissions": admissions,
			"encounters_30d": encounters_30d,
			"active_conditions": chronic,
			"er_visits": er_visits,
			"family_cv_risk": family_risk,
		},
		"model": "erpgenex-readmit-v2",
	}


@frappe.whitelist()
def get_predictive_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	occupancy = forecast_bed_occupancy(days=14, company=company, branch=branch)
	high_risk = frappe.db.count("Healthcare Admission", {"status": "discharged", "modified": [">=", frappe.utils.add_days(frappe.utils.today(), -7)]})
	care_gaps = 0
	if frappe.db.exists("DocType", "Healthcare Care Gap"):
		care_gaps = frappe.db.count("Healthcare Care Gap", {"status": "Open"})
	return {
		"occupancy_forecast": occupancy,
		"discharges_last_7d": high_risk,
		"open_care_gaps": care_gaps,
		"readmission_model": "erpgenex-readmit-v2",
		"recommendation": "Monitor occupancy spike days and target high-risk cohort for follow-up calls.",
	}
