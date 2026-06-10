# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Silent ERP billing account for patients — no Customer UI in healthcare workflows."""

from __future__ import annotations

import frappe
from frappe import _


def ensure_patient_billing_account(patient) -> str | None:
	"""Create or resolve the hidden accounting party linked to a Healthcare Patient."""
	doc = patient if hasattr(patient, "doctype") else frappe.get_doc("Healthcare Patient", patient)
	if doc.billing_customer:
		return doc.billing_customer

	company = doc.company
	if not company:
		return None

	mrn = _primary_mrn(doc)
	label = (doc.full_name or f"{doc.given_name} {doc.family_name}").strip()
	party_name = f"HP-{mrn}" if mrn else f"HP-{label}"[:140]
	customer = frappe.db.get_value("Customer", {"customer_name": party_name, "company": company}, "name")
	if not customer:
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": party_name,
				"company": company,
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True).name

	if doc.name and frappe.db.exists("Healthcare Patient", doc.name):
		frappe.db.set_value("Healthcare Patient", doc.name, "billing_customer", customer, update_modified=False)
	else:
		doc.billing_customer = customer
	return customer


def ensure_patient_identifiers(patient) -> None:
	"""Ensure at least one official MRN exists (FHIR Patient.identifier)."""
	doc = patient if hasattr(patient, "doctype") else frappe.get_doc("Healthcare Patient", patient)
	rows = doc.identifiers or []
	if any((r.identifier_type or "") == "MRN" and (r.value or "").strip() for r in rows):
		return
	mrn = f"MRN-{doc.name}" if doc.name else frappe.generate_hash(length=8).upper()
	doc.append(
		"identifiers",
		{
			"identifier_use": "official",
			"identifier_type": "MRN",
			"value": mrn,
			"is_primary_mrn": 1,
		},
	)


def _primary_mrn(doc) -> str | None:
	for row in doc.identifiers or []:
		if row.identifier_type == "MRN" and row.is_primary_mrn and (row.value or "").strip():
			return row.value.strip()
	for row in doc.identifiers or []:
		if row.identifier_type == "MRN" and (row.value or "").strip():
			return row.value.strip()
	return None
