# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.terminology import (
	get_patient_terminology_messages,
	is_healthcare_activity,
)


class TestHealthcareTerminology(FrappeTestCase):
	def test_is_healthcare_activity_explicit(self):
		self.assertTrue(is_healthcare_activity("Healthcare"))
		self.assertFalse(is_healthcare_activity("Trading"))

	def test_arabic_customer_maps_to_patient(self):
		terms = get_patient_terminology_messages("ar")
		self.assertEqual(terms.get("Customer"), "مريض")
		self.assertEqual(terms.get("Customers"), "مرضى")
