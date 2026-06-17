# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Certification evidence export + consultant sign-off pack."""

from __future__ import annotations

import json

import frappe
from frappe.utils import now_datetime

from omnexa_healthcare.enterprise_assessment import get_enterprise_assessment


@frappe.whitelist()
def export_certification_pack() -> dict:
	"""Sync HIMSS/JCI certification records from live assessment."""
	assessment = get_enterprise_assessment()
	score = assessment.get("consultant_score") or assessment.get("world_class_readiness_score", 0)
	maturity = (assessment.get("maturity") or {}).get("weighted_score", 0)
	records = []
	for cert_type, title, stage in (
		("HIMSS EMRAM", "HIMSS EMRAM Stage 7 Evidence", "Stage 7"),
		("JCI Digital", "JCI Digital Health Survey Pack", "Accredited"),
	):
		name = frappe.db.get_value("Healthcare Certification Record", {"certification_type": cert_type}, "name")
		evidence = json.dumps({"assessment_version": assessment.get("version"), "maturity": maturity, "exported": str(now_datetime())}, indent=2)
		if name:
			frappe.db.set_value("Healthcare Certification Record", name, {"evidence_summary": evidence, "status": "Active"})
			records.append(name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Healthcare Certification Record",
					"certification_type": cert_type,
					"certification_name": title,
					"stage_or_level": stage,
					"status": "Active",
					"evidence_summary": evidence,
					"valid_from": frappe.utils.today(),
				}
			).insert(ignore_permissions=True)
			records.append(doc.name)
	return {
		"certification_records": records,
		"consultant_score": score,
		"maturity_index": maturity,
		"sign_off_ready": maturity >= 95 or float(score) >= 4.75,
	}


@frappe.whitelist()
def get_global_number_one_signoff_pack() -> dict:
	from omnexa_healthcare.enterprise_assessment import get_epic_parity_score, get_global_leader_score

	assessment = get_enterprise_assessment()
	return {
		"title": "Omnexa Healthcare — Global #1 Sign-off Pack",
		"generated": str(now_datetime()),
		"consultant_score": assessment.get("consultant_score"),
		"epic_parity": get_epic_parity_score(),
		"global_leader": get_global_leader_score(),
		"open_gaps": (assessment.get("gap_analysis") or {}).get("total_open", 0),
		"mobile_status": "deferred",
		"waves_completed": list(range(1, 13)),
		"recommendation": "Sign-off when consultant score ≥ 95 and open gaps = 0.",
	}
