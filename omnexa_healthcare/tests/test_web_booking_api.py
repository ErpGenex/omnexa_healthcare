# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from omnexa_healthcare.api.web_booking import book_appointment_online, get_booking_slots, get_published_services
from omnexa_healthcare.utils.branch_demo_seed import (
	reset_healthcare_demo_for_branch,
	seed_healthcare_hospital_demo,
)


class TestHealthcareWebBookingAPI(FrappeTestCase):
	def setUp(self):
		companies = frappe.get_all("Company", pluck="name", limit=1)
		self.company = companies[0] if companies else None
		self.branch = frappe.db.get_value("Branch", {"company": self.company}, "name") if self.company else None
		if not (self.company and self.branch):
			self.skipTest("No company/branch for web booking test")
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)
		seed_healthcare_hospital_demo(self.company, self.branch, patients=5, force=1, include_financial=0)

	def tearDown(self):
		reset_healthcare_demo_for_branch(self.company, self.branch, dry_run=0)

	def test_get_published_services(self):
		rows = get_published_services(self.company, self.branch)
		self.assertGreaterEqual(len(rows), 8)
		self.assertTrue(all(row.get("service_code") for row in rows))

	def test_book_appointment_online_creates_portal_user(self):
		rows = get_published_services(self.company, self.branch)
		self.assertTrue(rows)
		service = next((row for row in rows if row.get("default_practitioner")), None)
		if not service:
			self.skipTest("No published service with default practitioner")
		slot_date = getdate(today())
		slots = []
		for _ in range(14):
			payload = get_booking_slots(self.company, self.branch, service["service_code"], str(slot_date))
			slots = payload.get("slots") or []
			if slots:
				break
			slot_date = add_days(slot_date, 1)
		if not slots:
			self.skipTest("No demo booking slots available in the next two weeks")

		phone = f"+966599{frappe.generate_hash(length=6)[:6]}"
		email = f"booking-{frappe.generate_hash(length=8)}@example.com"
		result = book_appointment_online(
			{
				"company": self.company,
				"branch": self.branch,
				"service_code": service["service_code"],
				"given_name": "Web",
				"family_name": "Patient",
				"phone": phone,
				"email": email,
				"appointment_date": slots[0]["start"],
				"slot_end": slots[0]["end"],
			}
		)
		self.assertTrue(result.get("name"))
		self.assertTrue(result.get("patient"))
		self.assertEqual(frappe.db.get_value("User", email, "email"), email)
		self.assertTrue(
			frappe.db.exists("Has Role", {"parent": email, "role": ["in", ["Patient Portal User", "Customer"]]})
		)
