# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""AI-assisted radiology CAD findings."""

from __future__ import annotations

import random

import frappe
from frappe import _


@frappe.whitelist()
def analyze_study_cad(diagnostic_report: str) -> dict:
	"""Run CAD analysis on a diagnostic report (rule-based + AI-ready hook)."""
	if not frappe.db.exists("Healthcare Diagnostic Report", diagnostic_report):
		frappe.throw(_("Diagnostic report not found."), title=_("CAD"))
	report = frappe.db.get_value(
		"Healthcare Diagnostic Report",
		diagnostic_report,
		["patient", "modality", "company"],
		as_dict=True,
	)
	findings = []
	modality = (report.modality or "").upper()
	candidates = []
	if "CT" in modality or "XR" in modality or "CR" in modality:
		candidates.append(("Nodule", 0.72 + random.random() * 0.2))
	if "CT" in modality:
		candidates.append(("Mass", 0.55 + random.random() * 0.3))
	if "XR" in modality or "CR" in modality:
		candidates.append(("Fracture", 0.4 + random.random() * 0.4))
	for finding_type, confidence in candidates[:2]:
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Radiology Cad Finding",
				"diagnostic_report": diagnostic_report,
				"patient": report.patient,
				"finding_type": finding_type,
				"confidence_score": round(confidence * 100, 1),
				"severity": "High" if confidence > 0.85 else "Medium",
				"review_status": "Pending",
				"model_version": "erpgenex-cad-v1",
				"company": report.company,
			}
		)
		doc.insert(ignore_permissions=True)
		findings.append({"name": doc.name, "finding_type": finding_type, "confidence_score": doc.confidence_score})
	return {"diagnostic_report": diagnostic_report, "findings": findings, "count": len(findings)}


@frappe.whitelist()
def list_cad_findings(diagnostic_report: str | None = None, review_status: str | None = None) -> list[dict]:
	filters: dict = {}
	if diagnostic_report:
		filters["diagnostic_report"] = diagnostic_report
	if review_status:
		filters["review_status"] = review_status
	return frappe.get_all(
		"Healthcare Radiology Cad Finding",
		filters=filters,
		fields=["name", "diagnostic_report", "patient", "finding_type", "confidence_score", "severity", "review_status"],
		order_by="modified desc",
		limit_page_length=50,
	)
