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

	def _make_patient(self, company, branch, given="John", family="Doe", mrn="MRN-001"):
		return frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company,
				"branch": branch,
				"given_name": given,
				"family_name": family,
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": mrn,
						"is_primary_mrn": 1,
					}
				],
				"telecom": [
					{"contact_system": "phone", "contact_use": "mobile", "value": "+10000000000", "rank": 1}
				],
			}
		).insert(ignore_permissions=True)

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
		patient = self._make_patient(company, branch)
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
					"naming_series": "HAP-.#####",
					"patient": patient.name,
					"company": company,
					"branch": branch,
					"department": department.name,
					"service_unit": unit.name,
					"appointment_date": "2026-04-20 10:00:00",
					"status": "Scheduled",
				}
			).insert(ignore_permissions=True)

	def test_patient_mrn_requires_single_primary(self):
		company = self._make_company("H")
		branch = self._make_branch(company, "HCH")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Patient",
					"naming_series": "HP-.#####",
					"company": company,
					"branch": branch,
					"given_name": "A",
					"family_name": "B",
					"identifiers": [
						{
							"identifier_use": "official",
							"identifier_type": "MRN",
							"value": "X1",
							"is_primary_mrn": 0,
						},
						{
							"identifier_use": "official",
							"identifier_type": "MRN",
							"value": "X2",
							"is_primary_mrn": 0,
						},
					],
				}
			).insert(ignore_permissions=True)

	def test_patient_full_name_and_non_mrn_identifier(self):
		company = self._make_company("I")
		branch = self._make_branch(company, "HCI")
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company,
				"branch": branch,
				"given_name": "Sam",
				"family_name": "User",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "National ID",
						"value": "29901011234567",
						"is_primary_mrn": 0,
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertIn("Sam", doc.full_name)
		self.assertIn("User", doc.full_name)

	def test_encounter_links_appointment_and_patient(self):
		company = self._make_company("J")
		branch = self._make_branch(company, "HCJ")
		patient = self._make_patient(company, branch, mrn="MRN-J-1")
		department = frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "General",
				"department_code": "GEN",
				"company": company,
				"branch": branch,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		unit = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"unit_name": "OPD-1",
				"unit_code": "OP1",
				"company": company,
				"branch": branch,
				"department": department.name,
				"unit_type": "Clinic",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		appt = frappe.get_doc(
			{
				"doctype": "Healthcare Appointment",
				"naming_series": "HAP-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"department": department.name,
				"service_unit": unit.name,
				"appointment_date": "2026-05-01 09:00:00",
				"status": "Scheduled",
			}
		).insert(ignore_permissions=True)
		enc = frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": patient.name,
				"appointment": appt.name,
				"company": company,
				"branch": branch,
				"department": department.name,
				"service_unit": unit.name,
				"encounter_class": "ambulatory",
				"encounter_type": "OPD",
				"status": "in-progress",
				"period_start": "2026-05-01 09:05:00",
				"diagnoses": [
					{
						"rank": 1,
						"icd10_code": "J00",
						"description": "Acute nasopharyngitis",
						"clinical_status": "active",
						"verification_status": "provisional",
					}
				],
			}
		).insert(ignore_permissions=True)
		appt.reload()
		self.assertEqual(appt.encounter, enc.name)

	def test_second_encounter_same_appointment_rejected(self):
		company = self._make_company("K")
		branch = self._make_branch(company, "HCK")
		patient = self._make_patient(company, branch, mrn="MRN-K-1")
		department = frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "Ortho",
				"department_code": "ORT",
				"company": company,
				"branch": branch,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		unit = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"unit_name": "Ortho-1",
				"unit_code": "O1",
				"company": company,
				"branch": branch,
				"department": department.name,
				"unit_type": "Clinic",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		appt = frappe.get_doc(
			{
				"doctype": "Healthcare Appointment",
				"naming_series": "HAP-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"department": department.name,
				"service_unit": unit.name,
				"appointment_date": "2026-05-02 10:00:00",
				"status": "Scheduled",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": patient.name,
				"appointment": appt.name,
				"company": company,
				"branch": branch,
				"department": department.name,
				"service_unit": unit.name,
				"encounter_class": "ambulatory",
				"encounter_type": "OPD",
				"status": "planned",
				"period_start": "2026-05-02 10:00:00",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Encounter",
					"naming_series": "ENC-.#####",
					"patient": patient.name,
					"appointment": appt.name,
					"company": company,
					"branch": branch,
					"department": department.name,
					"service_unit": unit.name,
					"encounter_class": "ambulatory",
					"encounter_type": "OPD",
					"status": "planned",
					"period_start": "2026-05-02 11:00:00",
				}
			).insert(ignore_permissions=True)
