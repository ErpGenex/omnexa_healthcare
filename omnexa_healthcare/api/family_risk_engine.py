# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Family Medicine — hereditary risk scoring v1."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, today

_CATEGORY_WEIGHTS: dict[str, tuple[int, int]] = {
	"Diabetes": (18, 10),
	"Hypertension": (12, 7),
	"Heart Disease": (15, 9),
	"Cancer": (14, 8),
	"Genetic Disorder": (20, 12),
	"Psychiatric": (8, 5),
	"Chronic Other": (6, 4),
}

_FIRST_DEGREE = {"Self", "Father", "Mother", "Sibling", "Child"}


def _score_category(entries: list[dict], category: str) -> tuple[int, list[str]]:
	first_w, other_w = _CATEGORY_WEIGHTS.get(category, (5, 3))
	score = 0
	factors: list[str] = []
	for row in entries:
		if row.get("condition_category") != category:
			continue
		rel = row.get("relative_relationship") or "Other"
		weight = first_w if rel in _FIRST_DEGREE else other_w
		score += weight
		factors.append(f"{category}:{rel}:{row.get('condition_description') or ''}")
	return min(score, 100), factors


def _compute_scores(history: list[dict]) -> dict:
	cardio = 0
	diabetes = 0
	all_factors: list[str] = []
	for cat in _CATEGORY_WEIGHTS:
		partial, factors = _score_category(history, cat)
		all_factors.extend(factors)
		if cat in ("Heart Disease", "Hypertension"):
			cardio = max(cardio, partial)
		if cat == "Diabetes":
			diabetes = max(diabetes, partial)
		if cat in ("Genetic Disorder", "Cancer"):
			cardio = max(cardio, int(partial * 0.7))
			diabetes = max(diabetes, int(partial * 0.5))

	overall = max(cardio, diabetes)
	if overall >= 70:
		level = "Critical"
	elif overall >= 45:
		level = "High"
	elif overall >= 25:
		level = "Medium"
	else:
		level = "Low"

	recommendations = []
	if diabetes >= 25:
		recommendations.append(_("Annual HbA1c screening and lifestyle counseling."))
	if cardio >= 25:
		recommendations.append(_("Blood pressure monitoring and lipid profile every 6–12 months."))
	if any(h.get("condition_category") == "Cancer" for h in history):
		recommendations.append(_("Consider age-appropriate cancer screening per guidelines."))
	if not recommendations:
		recommendations.append(_("Maintain routine preventive care schedule."))

	return {
		"cardiovascular_risk_score": cardio,
		"diabetes_risk_score": diabetes,
		"overall_risk_level": level,
		"risk_factors_json": json.dumps(all_factors[:20]),
		"recommendations": "\n".join(recommendations),
	}


@frappe.whitelist()
def compute_family_risk(family_unit: str, patient: str | None = None) -> dict:
	history = frappe.get_all(
		"Healthcare Family History",
		filters={"family_unit": family_unit},
		fields=[
			"condition_category",
			"condition_description",
			"relative_relationship",
			"patient",
			"age_at_onset",
		],
	)
	if patient:
		history = [h for h in history if not h.patient or h.patient == patient] + [
			h for h in history if h.relative_relationship != "Self"
		]
	scores = _compute_scores(history)
	unit = frappe.db.get_value("Healthcare Family Unit", family_unit, ["company", "branch"], as_dict=True)
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Family Risk Score",
			"family_unit": family_unit,
			"patient": patient,
			"assessment_date": today(),
			"cardiovascular_risk_score": scores["cardiovascular_risk_score"],
			"diabetes_risk_score": scores["diabetes_risk_score"],
			"overall_risk_level": scores["overall_risk_level"],
			"risk_factors_json": scores["risk_factors_json"],
			"recommendations": scores["recommendations"],
			"computed_by": frappe.session.user,
			"company": unit.company if unit else None,
			"branch": unit.branch if unit else None,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"ok": True, "name": doc.name, **scores}


@frappe.whitelist()
def get_latest_risk_scores(family_unit: str, limit: int = 5) -> list[dict]:
	limit = min(int(limit or 5), 20)
	return frappe.get_all(
		"Healthcare Family Risk Score",
		filters={"family_unit": family_unit},
		fields=[
			"name",
			"patient",
			"assessment_date",
			"cardiovascular_risk_score",
			"diabetes_risk_score",
			"overall_risk_level",
			"recommendations",
		],
		limit=limit,
		order_by="assessment_date desc, creation desc",
	)
