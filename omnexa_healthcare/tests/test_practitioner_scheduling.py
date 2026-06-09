# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.scheduling_engine import get_available_slots, validate_practitioner_appointment
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, make_test_branch, setup_admin_all_branch_access


class TestPractitionerScheduling(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def _company_branch(self, label):
		abbr = f"HC{label}{frappe.generate_hash(length=2).upper()}"
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"HC Co {label}",
				"abbr": abbr,
				"default_currency": "EGP",
				"country": "Egypt",
				"status": "Active",
			}
		).insert(ignore_permissions=True).name
		branch = frappe.get_doc(
			{"doctype": "Branch", "company": company, "branch_name": f"B{label}", "branch_code": label, "status": "Active", "eta_usb_signing_pin": "0000"}
		)
		branch.flags.ignore_mandatory = True
		branch.insert(ignore_permissions=True)
		return company, branch.name

	def _specialty(self, code="GEN"):
		name = f"Spec {code}"
		if frappe.db.exists("Healthcare Specialty", code):
			return code
		frappe.get_doc(
			{"doctype": "Healthcare Specialty", "specialty_name": name, "specialty_code": code, "is_active": 1}
		).insert(ignore_permissions=True)
		return code

	def test_multi_branch_practitioner_slots(self):
		company, branch_a = self._company_branch("A")
		branch_b = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company,
				"branch_name": "Branch B",
				"branch_code": "AB",
				"status": "Active",
				"eta_usb_signing_pin": "0000",
			}
		)
		branch_b.flags.ignore_mandatory = True
		branch_b.insert(ignore_permissions=True)
		branch_b = branch_b.name
		spec = self._specialty("GEN")
		pr = frappe.get_doc(
			{
				"doctype": "Healthcare Practitioner",
				"practitioner_name": "Dr Multi",
				"company": company,
				"status": "Active",
				"branch_assignments": [
					{"branch": branch_a, "specialty": spec, "consultation_fee": 200, "is_active": 1},
					{"branch": branch_b, "specialty": spec, "consultation_fee": 250, "is_active": 1},
				],
				"schedule": [
					{
						"branch": branch_a,
						"day_of_week": "Monday",
						"from_time": "09:00:00",
						"to_time": "10:00:00",
						"slot_duration_mins": 30,
						"specialty": spec,
					}
				],
			}
		).insert(ignore_permissions=True)
		# find next Monday
		from frappe.utils import getdate, today

		d = getdate(today())
		while d.strftime("%A") != "Monday":
			from frappe.utils import add_days

			d = add_days(d, 1)
		slots = get_available_slots(pr.name, branch_a, str(d), specialty=spec)
		self.assertEqual(len(slots), 2)
		branches = {row.branch for row in pr.branch_assignments}
		self.assertIn(branch_a, branches)
		self.assertIn(branch_b, branches)

	def test_unassigned_branch_rejected(self):
		company, branch = self._company_branch("X")
		other = self._company_branch("Y")[1]
		spec = self._specialty("ENT")
		pr = frappe.get_doc(
			{
				"doctype": "Healthcare Practitioner",
				"practitioner_name": "Dr One",
				"company": company,
				"branch_assignments": [{"branch": branch, "specialty": spec, "is_active": 1}],
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(Exception):
			validate_practitioner_appointment(
				practitioner=pr.name,
				branch=other,
				specialty=spec,
				slot_start="2026-06-09 10:00:00",
				slot_end="2026-06-09 10:15:00",
			)
