# -*- coding: utf-8 -*-
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestTelemedicine(FrappeTestCase):
	def setUp(self):
		frappe.db.rollback()
		self.company, self.branch = self._get_company_branch()
		if not self.company:
			self.skipTest("No company/branch available")

	def _get_company_branch(self):
		company = frappe.db.get_value("Company", {"name": "MH"}, "name") or frappe.db.get_value(
			"Company", {}, "name"
		)
		branch = None
		if company:
			branch = frappe.db.get_value("Branch", {"name": "MH-HO"}, "name") or frappe.db.get_value(
				"Branch", {"company": company}, "name"
			)
		return company, branch

	def _get_existing_patient(self):
		patient = frappe.db.get_value(
			"Healthcare Patient",
			{"company": self.company, "branch": self.branch},
			"name",
		)
		if patient:
			return frappe.get_doc("Healthcare Patient", patient)
		return self._create_test_patient("900")

	def _get_existing_practitioner(self):
		practitioner = frappe.db.get_value(
			"Healthcare Practitioner",
			{"company": self.company, "status": "Active"},
			"name",
		)
		if practitioner:
			return frappe.get_doc("Healthcare Practitioner", practitioner)
		return self._create_test_practitioner("900")

	def _create_test_patient(self, suffix="001"):
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": self.company,
				"branch": self.branch,
				"given_name": "Tele",
				"family_name": f"Patient{suffix}",
				"gender": "female",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": f"TEL-MRN-{suffix}",
						"is_primary_mrn": 1,
					}
				],
				"telecom": [
					{
						"contact_system": "phone",
						"contact_use": "mobile",
						"value": f"+20100000{suffix[-3:]}",
						"rank": 1,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def _create_test_practitioner(self, suffix="001"):
		specialty = frappe.db.get_value("Healthcare Specialty", {}, "name")
		if not specialty:
			self.skipTest("No healthcare specialty available")

		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Practitioner",
				"practitioner_name": f"Dr. Tele Test {suffix}",
				"company": self.company,
				"status": "Active",
				"branch_assignments": [
					{
						"branch": self.branch,
						"specialty": specialty,
						"is_active": 1,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def _session_payload(self, patient, practitioner):
		return {
			"patient": patient.name,
			"practitioner": practitioner.name,
			"session_type": "Video",
			"scheduled_datetime": now_datetime(),
			"company": self.company,
			"branch": self.branch,
		}

	def test_create_telemedicine_session(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()

		from omnexa_healthcare.api.telemedicine import create_telemedicine_session

		result = create_telemedicine_session(self._session_payload(patient, practitioner))
		self.assertTrue(result.get("success"))
		self.assertIsNotNone(result.get("session_id"))

	def test_start_telemedicine_session(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()

		from omnexa_healthcare.api.telemedicine import create_telemedicine_session, start_telemedicine_session

		session_result = create_telemedicine_session(self._session_payload(patient, practitioner))
		result = start_telemedicine_session(session_result.get("session_id"))
		self.assertTrue(result.get("success"))
		self.assertEqual(result.get("status"), "In Progress")

	def test_end_telemedicine_session(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()

		from omnexa_healthcare.api.telemedicine import (
			create_telemedicine_session,
			start_telemedicine_session,
			end_telemedicine_session,
		)

		session_result = create_telemedicine_session(self._session_payload(patient, practitioner))
		start_telemedicine_session(session_result.get("session_id"))
		result = end_telemedicine_session(
			session_result.get("session_id"),
			{
				"diagnosis": None,
				"clinical_notes": "Test clinical notes",
				"technical_quality": "Good",
				"rating": 5,
			},
		)
		self.assertTrue(result.get("success"))
		self.assertEqual(result.get("status"), "Completed")

	def test_register_monitoring_device(self):
		patient = self._get_existing_patient()

		from omnexa_healthcare.api.telemedicine_monitoring import register_device

		result = register_device(
			{
				"device_name": "Test Blood Pressure Monitor",
				"device_type": "Blood Pressure Monitor",
				"manufacturer": "Test Manufacturer",
				"model": "Test Model",
				"serial_number": "TEST123",
				"patient": patient.name,
				"connection_type": "Bluetooth",
				"company": self.company,
				"branch": self.branch,
			}
		)
		self.assertTrue(result.get("success"))
		self.assertIsNotNone(result.get("device_id"))

	def test_sync_device_reading(self):
		patient = self._get_existing_patient()

		from omnexa_healthcare.api.telemedicine_monitoring import register_device, sync_device_reading

		device_result = register_device(
			{
				"device_name": "Test Blood Pressure Monitor",
				"device_type": "Blood Pressure Monitor",
				"manufacturer": "Test Manufacturer",
				"model": "Test Model",
				"serial_number": "TEST124",
				"patient": patient.name,
				"connection_type": "Bluetooth",
				"company": self.company,
				"branch": self.branch,
			}
		)

		result = sync_device_reading(
			{
				"device_identifier": device_result.get("device_identifier"),
				"metric_type": "Blood Pressure",
				"value": 120,
				"unit": "mmHg",
				"alert_threshold_min": 90,
				"alert_threshold_max": 140,
			}
		)
		self.assertTrue(result.get("success"))
		self.assertIsNotNone(result.get("reading_id"))

	def test_get_session_stats(self):
		from omnexa_healthcare.api.telemedicine_admin import get_session_stats

		result = get_session_stats()
		self.assertTrue(result.get("success"))
		self.assertIn("stats", result)
		self.assertIn("total_sessions", result["stats"])

	def test_get_system_health(self):
		from omnexa_healthcare.api.telemedicine_admin import get_system_health

		result = get_system_health()
		self.assertTrue(result.get("success"))
		self.assertIn("health", result)

	def test_get_portal_config(self):
		from omnexa_healthcare.api.telemedicine import get_portal_config

		result = get_portal_config()
		self.assertTrue(result.get("success"))
		self.assertIn("config", result)

	def test_get_dashboard_stats(self):
		from omnexa_healthcare.api.telemedicine_admin import get_dashboard_stats

		result = get_dashboard_stats()
		self.assertTrue(result.get("success"))
		self.assertIn("stats", result)

	def test_get_available_slots(self):
		practitioner = self._get_existing_practitioner()
		from omnexa_healthcare.api.telemedicine import get_available_slots

		result = get_available_slots(practitioner.name, now_datetime().strftime("%Y-%m-%d"))
		self.assertTrue(result.get("success"))
		self.assertTrue(result.get("slots"))

	def test_book_telemedicine_consultation(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		from omnexa_healthcare.api.telemedicine import book_telemedicine_consultation

		result = book_telemedicine_consultation(
			{
				"patient": patient.name,
				"practitioner": practitioner.name,
				"date": now_datetime().strftime("%Y-%m-%d"),
				"time": "10:00:00",
				"session_type": "video",
			}
		)
		self.assertTrue(result.get("success"))
