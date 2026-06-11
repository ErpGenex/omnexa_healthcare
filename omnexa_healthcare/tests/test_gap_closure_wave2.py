# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.enterprise_assessment import get_enterprise_assessment
from omnexa_healthcare.gap_closure_wave2_defs import GAP_CLOSURE_WAVE2_DOCTYPES


class TestGapClosureWave2(unittest.TestCase):
	def test_wave2_doctypes_exist(self):
		for spec in GAP_CLOSURE_WAVE2_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", spec["name"]), spec["name"])

	def test_wave2_pages_exist(self):
		for page in ("healthcare-nursing-portal", "healthcare-telehealth-room", "healthcare-patient-consumer"):
			self.assertTrue(frappe.db.exists("Page", page), page)

	def test_critical_gaps_closed_in_assessment(self):
		assessment = get_enterprise_assessment()
		strategic = assessment["gap_analysis"]["strategic_gaps"]
		critical_done = [s for s in strategic if s["priority"] == "Critical" and s["status"] == "completed"]
		self.assertGreaterEqual(len(critical_done), 8)

	def test_patient_otp_roundtrip(self):
		frappe.db.set_single_value("Healthcare Settings", "enable_patient_otp", 1)
		from omnexa_healthcare.api.patient_otp import send_patient_otp, verify_patient_otp

		sent = send_patient_otp("0501234567")
		self.assertTrue(sent["ok"])
		otp = sent.get("demo_otp")
		if not otp and frappe.conf.developer_mode:
			self.skipTest("No demo OTP")
		if otp:
			verified = verify_patient_otp("0501234567", otp)
			self.assertTrue(verified["ok"])
			self.assertTrue(verified.get("session_token"))

	def test_telehealth_session_create(self):
		frappe.db.set_single_value("Healthcare Settings", "enable_telehealth_video", 1)
		appt = frappe.db.get_value("Healthcare Appointment", {}, "name")
		if not appt:
			self.skipTest("No appointment")
		from omnexa_healthcare.api.telehealth import create_telehealth_session

		result = create_telehealth_session(appt)
		self.assertTrue(result.get("room_id"))
		self.assertTrue(result.get("join_url"))

	def test_maturity_domains_wave2(self):
		assessment = get_enterprise_assessment()
		domain_ids = {d["id"] for d in assessment["maturity"]["domains"]}
		for expected in ("home_healthcare", "nursing_portal", "telemedicine", "patient_portal"):
			self.assertIn(expected, domain_ids)
