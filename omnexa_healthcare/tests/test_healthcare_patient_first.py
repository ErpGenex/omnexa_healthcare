# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.patient_billing import ensure_patient_billing_account


class TestHealthcarePatientFirst(FrappeTestCase):
	def test_patient_auto_billing_without_customer_field(self):
		company = frappe.get_all("Company", pluck="name", limit=1)
		branch = frappe.db.get_value("Branch", {"company": company[0]}, "name") if company else None
		if not (company and branch):
			self.skipTest("No company/branch")

		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company[0],
				"branch": branch,
				"given_name": "Test",
				"family_name": "PatientFirst",
				"gender": "male",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": "TST-MRN-001",
						"is_primary_mrn": 1,
					}
				],
				"telecom": [{"contact_system": "phone", "contact_use": "mobile", "value": "+20100000099", "rank": 1}],
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.billing_customer)
		self.assertTrue(frappe.db.exists("Customer", doc.billing_customer))
		ensure_patient_billing_account(doc.name)
		frappe.delete_doc("Healthcare Patient", doc.name, force=1, ignore_permissions=True)
