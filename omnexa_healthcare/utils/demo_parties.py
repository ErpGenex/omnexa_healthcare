# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Demo / simulation parties — patients instead of customers when activity is Healthcare."""

from __future__ import annotations

import frappe
from frappe.utils import add_years, nowdate

from omnexa_healthcare.patient_billing import ensure_patient_billing_account
from omnexa_healthcare.terminology import is_healthcare_activity


def seed_simulation_patients(
	company: str,
	branch: str,
	count: int,
	*,
	prefix: str = "SIM",
) -> dict:
	"""Create Healthcare Patient records; return ERP billing account IDs for invoicing."""
	billing_accounts: list[str] = []
	patient_names: list[str] = []
	for idx in range(1, max(1, count) + 1):
		given = f"{prefix}{idx}"
		family = f"Patient-{branch[-6:]}"
		mrn = f"{prefix}-MRN-{branch}-{idx:02d}"
		existing = frappe.db.get_value(
			"Healthcare Patient Identifier",
			{"identifier_type": "MRN", "value": mrn, "parenttype": "Healthcare Patient"},
			"parent",
		)
		if existing and frappe.db.get_value("Healthcare Patient", existing, "branch") == branch:
			patient_names.append(existing)
			bc = frappe.db.get_value("Healthcare Patient", existing, "billing_customer")
			if bc:
				billing_accounts.append(bc)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company,
				"branch": branch,
				"given_name": given,
				"family_name": family,
				"gender": "unknown",
				"birth_date": add_years(nowdate(), -30),
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": mrn,
						"is_primary_mrn": 1,
					}
				],
				"telecom": [
					{
						"contact_system": "phone",
						"contact_use": "mobile",
						"value": f"+2010000{idx:04d}",
						"rank": 1,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		bc = ensure_patient_billing_account(doc) or doc.billing_customer
		patient_names.append(doc.name)
		if bc:
			billing_accounts.append(bc)

	return {"patients": patient_names, "billing_accounts": billing_accounts}


def seed_demo_patient_master(company: str, branch: str, tag: str) -> dict:
	"""Single demo patient for branch seed masters (replaces DEMO-CUST)."""
	mrn = f"DEMO-MRN-{tag}"
	existing = frappe.db.get_value(
		"Healthcare Patient Identifier",
		{"identifier_type": "MRN", "value": mrn, "parenttype": "Healthcare Patient"},
		"parent",
	)
	if existing:
		bc = frappe.db.get_value("Healthcare Patient", existing, "billing_customer")
		return {"patient": existing, "billing_customer": bc}

	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient",
			"naming_series": "HP-.#####",
			"company": company,
			"branch": branch,
			"given_name": "Demo",
			"family_name": f"Patient {tag}",
			"gender": "unknown",
			"identifiers": [
				{
					"identifier_use": "official",
					"identifier_type": "MRN",
					"value": mrn,
					"is_primary_mrn": 1,
				}
			],
			"telecom": [
				{"contact_system": "phone", "contact_use": "mobile", "value": "+20100000001", "rank": 1}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	bc = ensure_patient_billing_account(doc) or doc.billing_customer
	return {"patient": doc.name, "billing_customer": bc}


def should_use_patients(activity: str | None = None) -> bool:
	if not frappe.db.exists("DocType", "Healthcare Patient"):
		return False
	return is_healthcare_activity(activity)

