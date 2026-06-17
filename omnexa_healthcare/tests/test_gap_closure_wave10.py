# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe


class TestGapClosureWave10(unittest.TestCase):
	def test_fhir_medication_request_read(self):
		from omnexa_healthcare.api.fhir_rest import READ_MAP

		self.assertIn("MedicationRequest", READ_MAP)

	def test_fhir_bulk_export(self):
		from omnexa_healthcare.api.fhir_bulk_export import get_read_replica_guide

		guide = get_read_replica_guide()
		self.assertIn("recommendations", guide)

	def test_hl7_mllp(self):
		from omnexa_healthcare.api.hl7_messaging import hl7_mllp_listener_status

		status = hl7_mllp_listener_status()
		self.assertEqual(status.get("listener"), "active")

	def test_interop_settings(self):
		settings = frappe.get_doc("Healthcare Settings")
		self.assertTrue(hasattr(settings, "enable_fhir_bulk_export"))
