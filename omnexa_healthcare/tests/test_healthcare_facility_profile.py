import frappe
from frappe.tests.utils import FrappeTestCase


class TestHealthcareFacilityProfile(FrappeTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Currency", "EGP"):
			frappe.get_doc(
				{"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Country", "Egypt"):
			frappe.get_doc(
				{"doctype": "Country", "country_name": "Egypt", "code": "EG"}
			).insert(ignore_permissions=True)

	def _make_company(self, label):
		abbr = f"HC{label}{frappe.generate_hash(length=2).upper()}"
		doc = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"Healthcare Co {label}",
				"abbr": abbr,
				"default_currency": "EGP",
				"country": "Egypt",
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_branch(self, company, code):
		doc = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company,
				"branch_name": f"Branch {code}",
				"branch_code": code,
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def test_facility_profile_rejects_cross_company_branch(self):
		company_a = self._make_company("A")
		company_b = self._make_company("B")
		branch_b = self._make_branch(company_b, "HCB")
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Facility Profile",
				"facility_name": "Main Hospital",
				"company": company_a,
				"branch": branch_b,
				"facility_type": "Hospital",
				"status": "Active",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_facility_profile_inserts_with_same_company_branch(self):
		company = self._make_company("C")
		branch = self._make_branch(company, "HCC")
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Facility Profile",
				"facility_name": "Clinic One",
				"company": company,
				"branch": branch,
				"facility_type": "Clinic",
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Healthcare Facility Profile", doc.name))

	def test_department_code_unique_per_branch(self):
		company = self._make_company("D")
		branch = self._make_branch(company, "HCD")
		frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "Cardiology",
				"department_code": "CARD",
				"company": company,
				"branch": branch,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Department",
					"department_name": "Cardiology 2",
					"department_code": "CARD",
					"company": company,
					"branch": branch,
					"status": "Active",
				}
			).insert(ignore_permissions=True)

	def test_service_unit_company_must_match_branch_company(self):
		company_a = self._make_company("E")
		company_b = self._make_company("F")
		branch_b = self._make_branch(company_b, "HCF")
		department_b = frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "OPD",
				"department_code": "OPD",
				"company": company_b,
				"branch": branch_b,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Service Unit",
					"unit_name": "Clinic A1",
					"unit_code": "A1",
					"company": company_a,
					"branch": branch_b,
					"department": department_b.name,
					"unit_type": "Clinic",
					"status": "Active",
				}
			).insert(ignore_permissions=True)

	def test_inactive_service_unit_cannot_accept_appointment(self):
		company = self._make_company("G")
		branch = self._make_branch(company, "HCG")
		department = frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "Radiology",
				"department_code": "RAD",
				"company": company,
				"branch": branch,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		unit = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"unit_name": "Unit R1",
				"unit_code": "R1",
				"company": company,
				"branch": branch,
				"department": department.name,
				"unit_type": "Service Unit",
				"status": "Inactive",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Appointment",
					"patient_name": "Patient Test",
					"company": company,
					"branch": branch,
					"department": department.name,
					"service_unit": unit.name,
					"appointment_date": "2026-04-20 10:00:00",
					"status": "Scheduled",
				}
			).insert(ignore_permissions=True)
