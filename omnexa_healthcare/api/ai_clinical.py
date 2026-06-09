# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Clinical AI — risk flags, summaries, CDS augmentation."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def generate_patient_insights(patient: str) -> list[dict]:
	if not patient:
		frappe.throw(_("patient is required"))
	insights = []
	allergies = frappe.get_all("Healthcare Allergy Intolerance", filters={"patient": patient, "status": "active"}, pluck="substance")
	if allergies:
		insights.append(_store_insight(patient, "Alert", f"Active allergies: {', '.join(allergies)}", 0.95))
	abnormal = frappe.db.count("Healthcare Diagnostic Report", {"patient": patient, "abnormal_flag": 1})
	if abnormal:
		insights.append(_store_insight(patient, "Risk", f"{abnormal} abnormal lab/imaging report(s) on file.", 0.88))
	chronic = frappe.get_all("Healthcare Clinical Condition", filters={"patient": patient, "status": "active"}, pluck="condition")
	if chronic:
		insights.append(
			_store_insight(patient, "Recommendation", f"Review chronic conditions: {', '.join(chronic[:5])}", 0.82)
		)
	if not insights:
		insights.append(_store_insight(patient, "Summary", "No critical AI flags — continue standard care.", 0.75))
	return insights


@frappe.whitelist()
def generate_discharge_summary_draft(admission: str) -> dict:
	admit = frappe.get_doc("Healthcare Admission", admission)
	summary = frappe.get_doc(
		{
			"doctype": "Healthcare Discharge Summary",
			"admission": admission,
			"patient": admit.patient,
			"discharge_datetime": now_datetime(),
			"summary": _draft_discharge_text(admit),
			"company": admit.company,
			"branch": admit.branch,
		}
	).insert()
	return {"discharge_summary": summary.name, "html": summary.summary}


def _store_insight(patient: str, insight_type: str, summary: str, confidence: float) -> dict:
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Clinical Ai Insight",
			"patient": patient,
			"insight_type": insight_type,
			"summary": summary,
			"confidence": confidence * 100,
			"source": "omnexa_rules_v1",
			"company": company,
			"branch": branch,
		}
	).insert(ignore_permissions=True)
	return {"name": doc.name, "insight_type": insight_type, "summary": summary, "confidence": confidence}


def _draft_discharge_text(admit) -> str:
	patient = frappe.get_doc("Healthcare Patient", admit.patient)
	return (
		f"<h4>Discharge Summary</h4>"
		f"<p><b>Patient:</b> {patient.given_name} {patient.family_name}</p>"
		f"<p><b>Admission:</b> {admit.name} · {admit.admission_datetime}</p>"
		f"<p>AI-assisted draft — requires physician attestation.</p>"
	)
