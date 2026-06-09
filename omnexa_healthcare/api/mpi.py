# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Master Patient Index — duplicate detection and merge."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def find_duplicate_patients(patient: str | None = None, company: str | None = None) -> list[dict]:
	"""Find potential duplicate patients by name + birth date or shared identifier value."""
	filters = {"active": 1}
	if company:
		filters["company"] = company
	if patient:
		filters["name"] = ["!=", patient]

	candidates = frappe.get_all(
		"Healthcare Patient",
		filters=filters,
		fields=["name", "full_name", "birth_date", "company", "branch"],
		limit=500,
	)
	if patient:
		source = frappe.get_doc("Healthcare Patient", patient)
		return _match_patients(source, candidates)
	return _group_duplicates(candidates)


@frappe.whitelist()
def merge_patients(source_patient: str, target_patient: str, notes: str | None = None) -> dict:
	if source_patient == target_patient:
		frappe.throw(_("Source and target must differ"))
	if not frappe.has_permission("Healthcare Patient", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	source = frappe.get_doc("Healthcare Patient", source_patient)
	target = frappe.get_doc("Healthcare Patient", target_patient)
	_reassign_links(source_patient, target_patient)
	source.active = 0
	source.save(ignore_permissions=True)
	log = frappe.get_doc(
		{
			"doctype": "Healthcare Patient Merge Log",
			"source_patient": source_patient,
			"target_patient": target_patient,
			"merged_by": frappe.session.user,
			"merged_on": now_datetime(),
			"notes": notes,
		}
	).insert(ignore_permissions=True)
	return {"merge_log": log.name, "target_patient": target_patient}


def enforce_cross_branch_patient_policy(doc, method=None):
	"""Called from Healthcare Patient validate when settings restrict branch."""
	settings = frappe.get_cached_doc("Healthcare Settings")
	if settings.get("allow_cross_branch_patient_access"):
		return
	if not doc.is_new() and doc.has_value_changed("branch"):
		if not frappe.has_permission("Healthcare Patient", "write"):
			frappe.throw(_("Cross-branch patient moves require enterprise MPI policy."), title=_("MPI"))


def _reassign_links(source: str, target: str):
	for dt in (
		"Healthcare Appointment",
		"Healthcare Encounter",
		"Healthcare Episode Of Care",
		"Healthcare Service Charge",
		"Healthcare Admission",
		"Healthcare Lab Sample",
		"Healthcare Medication Dispense",
	):
		if frappe.db.exists("DocType", dt):
			frappe.db.sql(f"UPDATE `tab{dt}` SET patient = %s WHERE patient = %s", (target, source))


def _match_patients(source, candidates: list[dict]) -> list[dict]:
	matches = []
	for row in candidates:
		score = 0
		if row.full_name and source.full_name and row.full_name.lower() == source.full_name.lower():
			score += 2
		if row.birth_date and source.birth_date and str(row.birth_date) == str(source.birth_date):
			score += 2
		if score >= 2:
			matches.append({**row, "match_score": score})
	return matches


def _group_duplicates(candidates: list[dict]) -> list[dict]:
	seen: dict[tuple, list] = {}
	for row in candidates:
		key = ((row.full_name or "").lower(), str(row.birth_date or ""))
		seen.setdefault(key, []).append(row)
	return [{"key": k, "patients": v} for k, v in seen.items() if len(v) > 1]
