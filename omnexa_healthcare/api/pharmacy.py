# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Pharmacy — FEFO batch selection, interaction checks, eRx export."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


@frappe.whitelist()
def api_check_drug_interactions(patient: str, item: str) -> list[dict]:
	if not (patient and item):
		frappe.throw(_("patient and item are required"))
	current_meds = frappe.get_all(
		"Healthcare Medication Statement",
		filters={"patient": patient, "status": ["in", ["active", "on-hold"]]},
		pluck="medication_text",
	)
	current_meds = [m for m in current_meds if m and m != item]
	if not current_meds:
		return []
	rules = frappe.get_all(
		"Healthcare Drug Interaction Rule",
		filters={"is_active": 1},
		fields=["drug_a", "drug_b", "severity", "description"],
	)
	alerts = []
	for rule in rules:
		pair = {rule.drug_a, rule.drug_b}
		if item in pair and pair.intersection(current_meds):
			alerts.append(rule)
	# allergy cross-check
	allergies = frappe.get_all("Healthcare Allergy Intolerance", filters={"patient": patient, "status": "active"}, pluck="substance")
	if allergies and item in allergies:
		alerts.append({"severity": "Contraindicated", "description": _("Patient allergy to this substance")})
	return alerts


@frappe.whitelist()
def api_select_fefo_batch(item: str, warehouse: str, qty: float) -> dict:
	"""Select earliest-expiry batch if Item Batch exists in accounting."""
	qty = flt(qty)
	if frappe.db.exists("DocType", "Batch") and frappe.db.has_column("Batch", "expiry_date"):
		batch = frappe.db.sql(
			"""
			SELECT b.name, b.expiry_date, IFNULL(SLE.actual_qty, 0) AS qty
			FROM `tabBatch` b
			LEFT JOIN (
				SELECT batch_no, SUM(actual_qty) AS actual_qty
				FROM `tabStock Ledger Entry`
				WHERE item_code = %s AND warehouse = %s
				GROUP BY batch_no
			) SLE ON SLE.batch_no = b.name
			WHERE b.item = %s AND IFNULL(SLE.actual_qty, 0) >= %s
			ORDER BY b.expiry_date ASC
			LIMIT 1
			""",
			(item, warehouse, item, qty),
			as_dict=True,
		)
		if batch:
			return {"batch_no": batch[0].name, "expiry_date": batch[0].expiry_date}
	return {"batch_no": None, "expiry_date": None}


@frappe.whitelist()
def api_export_erx_pdf(medication_statement: str) -> dict:
	doc = frappe.get_doc("Healthcare Medication Statement", medication_statement)
	html = frappe.get_print("Healthcare Medication Statement", doc.name)
	return {"html": html, "medication_statement": doc.name}


@frappe.whitelist()
def api_pharmacy_pos_dispense(patient: str, item: str, qty: float, warehouse: str, branch: str, company: str) -> dict:
	alerts = api_check_drug_interactions(patient, item)
	if any(a.get("severity") == "Contraindicated" for a in alerts):
		frappe.throw(_("Contraindicated interaction — dispense blocked."), title=_("Pharmacy Safety"))
	batch = api_select_fefo_batch(item, warehouse, qty)
	md = frappe.get_doc(
		{
			"doctype": "Healthcare Medication Dispense",
			"naming_series": "MDP-.#####",
			"patient": patient,
			"company": company,
			"branch": branch,
			"item": item,
			"qty": flt(qty),
			"warehouse": warehouse,
			"batch_no": batch.get("batch_no"),
			"expiry_date": batch.get("expiry_date"),
			"status": "draft",
		}
	).insert(ignore_permissions=True)
	from omnexa_healthcare.api.dispensing import create_stock_entry_from_medication_dispense

	out = create_stock_entry_from_medication_dispense(md.name)
	return {"medication_dispense": md.name, "stock_entry": out.get("stock_entry"), "alerts": alerts}


@frappe.whitelist()
def api_list_active_medications(patient: str | None = None, branch: str | None = None) -> list[dict]:
	filters: dict = {"status": ["in", ["active", "on-hold"]]}
	if patient:
		filters["patient"] = patient
	if branch:
		filters["branch"] = branch
	return frappe.get_all(
		"Healthcare Medication Statement",
		filters=filters,
		fields=["name", "patient", "medication_text", "status", "branch", "company", "dosage_text"],
		order_by="modified desc",
		limit=100,
	)
