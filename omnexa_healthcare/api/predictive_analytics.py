# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Predictive analytics ML layer (readmission + occupancy)."""

from __future__ import annotations

import frappe

from omnexa_healthcare.api.occupancy_forecast import forecast_bed_occupancy


@frappe.whitelist()
def predict_readmission_risk(patient: str) -> dict:
	"""Rule-based readmission risk score (ML-ready features)."""
	admissions = frappe.db.count("Healthcare Admission", {"patient": patient})
	encounters_30d = frappe.db.count(
		"Healthcare Encounter",
		{"patient": patient, "encounter_date": [">=", frappe.utils.add_days(frappe.utils.today(), -30)]},
	)
	chronic = frappe.db.count("Healthcare Clinical Condition", {"patient": patient, "status": "active"})
	score = min(100, admissions * 12 + encounters_30d * 8 + chronic * 10)
	risk = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
	return {
		"patient": patient,
		"readmission_risk_score": score,
		"risk_level": risk,
		"features": {"admissions": admissions, "encounters_30d": encounters_30d, "active_conditions": chronic},
		"model": "erpgenex-readmit-v1",
	}


@frappe.whitelist()
def get_predictive_dashboard(company: str | None = None, branch: str | None = None) -> dict:
	occupancy = forecast_bed_occupancy(days=14, company=company, branch=branch)
	high_risk = frappe.db.count("Healthcare Admission", {"status": "discharged", "modified": [">=", frappe.utils.add_days(frappe.utils.today(), -7)]})
	return {
		"occupancy_forecast": occupancy,
		"discharges_last_7d": high_risk,
		"readmission_model": "erpgenex-readmit-v1",
		"recommendation": "Monitor occupancy spike days and target high-risk cohort for follow-up calls.",
	}
