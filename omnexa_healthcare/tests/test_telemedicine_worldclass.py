# -*- coding: utf-8 -*-
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestTelemedicineWorldClass(FrappeTestCase):
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
		return None

	def _get_existing_practitioner(self):
		practitioner = frappe.db.get_value(
			"Healthcare Practitioner",
			{"company": self.company, "status": "Active"},
			"name",
		)
		if practitioner:
			return frappe.get_doc("Healthcare Practitioner", practitioner)
		return None

	def _create_session(self, patient, practitioner):
		from omnexa_healthcare.api.telemedicine import create_telemedicine_session

		return create_telemedicine_session(
			{
				"patient": patient.name,
				"practitioner": practitioner.name,
				"session_type": "Video",
				"scheduled_datetime": now_datetime(),
				"company": self.company,
				"branch": self.branch,
			}
		)

	def test_session_access_token_roundtrip(self):
		from omnexa_healthcare.api.telemedicine_security import (
			generate_session_access_token,
			verify_session_access_token,
		)

		token = generate_session_access_token("TEST-SESSION", user="Administrator", role="participant")
		payload = verify_session_access_token(token, session_id="TEST-SESSION")
		self.assertEqual(payload.get("session_id"), "TEST-SESSION")
		self.assertEqual(payload.get("user"), "Administrator")

	def test_socket_config_and_auth(self):
		from omnexa_healthcare.api.telemedicine_socket import get_socket_auth_token, get_socket_config

		config = get_socket_config()
		self.assertTrue(config.get("success"))
		self.assertEqual(config["config"]["transport"], "frappe_realtime")

		auth = get_socket_auth_token(user="Administrator", session_id="socket-test")
		self.assertTrue(auth.get("success"))
		self.assertTrue(auth.get("token"))

	def test_jitsi_meeting_config(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		if not patient or not practitioner:
			self.skipTest("No patient/practitioner available")

		session_result = self._create_session(patient, practitioner)
		from omnexa_healthcare.api.telemedicine_video import get_jitsi_meeting_config

		config = get_jitsi_meeting_config(session_result["session_id"])
		self.assertTrue(config.get("success"))
		self.assertTrue(config.get("domain"))
		self.assertEqual(config.get("room_name"), session_result.get("room_id"))

	def test_join_payload(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		if not patient or not practitioner:
			self.skipTest("No patient/practitioner available")

		session_result = self._create_session(patient, practitioner)
		from omnexa_healthcare.api.telemedicine_integration import build_join_payload

		payload = build_join_payload(session_result["session_id"])
		self.assertTrue(payload.get("success"))
		self.assertTrue(payload.get("token"))
		self.assertIn("jitsi", payload)

	def test_session_chat_messages(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		if not patient or not practitioner:
			self.skipTest("No patient/practitioner available")

		session_result = self._create_session(patient, practitioner)
		from omnexa_healthcare.api.telemedicine_socket import (
			get_session_chat_messages,
			send_session_chat_message,
		)

		send_result = send_session_chat_message(session_result["session_id"], "Hello from world-class test")
		self.assertTrue(send_result.get("success"))

		history = get_session_chat_messages(session_result["session_id"])
		self.assertTrue(history.get("success"))
		self.assertGreaterEqual(len(history.get("messages") or []), 1)

	def test_fhir_bundle_export(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		if not patient or not practitioner:
			self.skipTest("No patient/practitioner available")

		session_result = self._create_session(patient, practitioner)
		from omnexa_healthcare.api.telemedicine import get_telemedicine_fhir_bundle

		result = get_telemedicine_fhir_bundle(session_result["session_id"])
		self.assertTrue(result.get("success"))
		bundle = result.get("bundle") or {}
		self.assertEqual(bundle.get("resourceType"), "Bundle")
		self.assertTrue(bundle.get("entry"))

	def test_finalize_creates_encounter_on_end(self):
		patient = self._get_existing_patient()
		practitioner = self._get_existing_practitioner()
		if not patient or not practitioner:
			self.skipTest("No patient/practitioner available")

		from omnexa_healthcare.api.telemedicine import (
			create_telemedicine_session,
			end_telemedicine_session,
			start_telemedicine_session,
		)

		session_result = create_telemedicine_session(
			{
				"patient": patient.name,
				"practitioner": practitioner.name,
				"session_type": "Video",
				"scheduled_datetime": now_datetime(),
				"company": self.company,
				"branch": self.branch,
			}
		)
		start_telemedicine_session(session_result["session_id"])
		end_result = end_telemedicine_session(
			session_result["session_id"],
			{"clinical_notes": "World-class integration test", "technical_quality": "Good", "rating": 5},
		)
		self.assertTrue(end_result.get("success"))

		encounter = frappe.db.get_value(
			"Healthcare Telemedicine Session", session_result["session_id"], "encounter"
		)
		self.assertTrue(encounter)
		self.assertTrue(frappe.db.exists("Healthcare Encounter", encounter))

	def test_patient_clinical_summary(self):
		patient = self._get_existing_patient()
		if not patient:
			self.skipTest("No patient available")

		from omnexa_healthcare.api.telemedicine import get_patient_clinical_summary

		result = get_patient_clinical_summary(patient.name)
		self.assertTrue(result.get("success"))
		self.assertIn("summary", result)

	def test_create_telemedicine_patient(self):
		practitioner = self._get_existing_practitioner()
		if not practitioner:
			self.skipTest("No practitioner available")

		from omnexa_healthcare.api.telemedicine import create_telemedicine_patient

		result = create_telemedicine_patient(
			{
				"full_name": "Tele Finish Patient",
				"gender": "female",
				"birth_date": "1990-01-01",
				"phone": "+201555000999",
				"practitioner": practitioner.name,
			}
		)
		self.assertTrue(result.get("success"))
		self.assertTrue(result.get("patient_id"))
