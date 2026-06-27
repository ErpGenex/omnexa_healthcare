# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""World-class gap closure — smoke and integration tests (80+ target)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.api.specialty_emr import SPECIALTY_FORMS, list_specialty_forms, validate_icd10_code
from omnexa_healthcare.healthcare_compliance import HEALTHCARE_COMPLIANCE_MATRIX, get_healthcare_compliance_score
from omnexa_healthcare.report_pack.executors import REPORT_SPECS, run_report
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, setup_admin_all_branch_access


class TestWorldClassClosure(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def test_compliance_score_world_class_gate(self):
		score = get_healthcare_compliance_score()
		self.assertGreaterEqual(score["weighted_score"], 4.5)

	def test_specialty_forms_catalog(self):
		forms = list_specialty_forms()
		self.assertGreaterEqual(len(forms), 10)

	def test_report_pack_registry_size(self):
		self.assertGreaterEqual(len(REPORT_SPECS), 38)

	def test_matrix_all_domains_above_three(self):
		for row in HEALTHCARE_COMPLIANCE_MATRIX:
			self.assertGreaterEqual(row["score"], 3.0, msg=row["id"])

	def test_icd10_validation_blocks_unknown(self):
		if not frappe.db.exists("Healthcare Icd10 Code", {"code": "Z99.99"}):
			with self.assertRaises(frappe.ValidationError):
				validate_icd10_code("Z99.99")

	def test_icd10_validation_allows_seeded(self):
		if frappe.db.exists("Healthcare Icd10 Code", {"code": "I10"}):
			validate_icd10_code("I10")

	def test_fhir_rest_read_patient_shape(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("no patient")
		from omnexa_healthcare.api.fhir_rest import fhir_read

		out = fhir_read("Patient", patient)
		self.assertEqual(out.get("resourceType"), "Patient")

	def test_hl7_adt_message_builds(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("no patient")
		from omnexa_healthcare.api.hl7_messaging import hl7_send_adt

		out = hl7_send_adt(patient)
		self.assertIn("ADT^", out["message"])

	def test_lab_worklist_api(self):
		branch = frappe.db.get_value("Branch", {}, "name")
		if not branch:
			self.skipTest("no branch")
		from omnexa_healthcare.api.lab_lis import api_get_lab_worklist

		self.assertIsInstance(api_get_lab_worklist(branch), list)

	def test_radiology_worklist_api(self):
		branch = frappe.db.get_value("Branch", {}, "name")
		if not branch:
			self.skipTest("no branch")
		from omnexa_healthcare.api.radiology import api_get_radiology_worklist

		self.assertIsInstance(api_get_radiology_worklist(branch), list)

	def test_drug_interaction_api(self):
		from omnexa_healthcare.api.pharmacy import api_check_drug_interactions

		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("no patient")
		self.assertIsInstance(api_check_drug_interactions(patient, "NONEXIST-ITEM"), list)

	def test_mpi_find_duplicates(self):
		from omnexa_healthcare.api.mpi import find_duplicate_patients

		self.assertIsInstance(find_duplicate_patients(), list)

	def test_specialty_form_keys(self):
		self.assertIn("General Medicine", SPECIALTY_FORMS)
		self.assertIn("Psychiatry", SPECIALTY_FORMS)


class TestReportPackSmoke(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()

	def _filters(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		return frappe._dict({"company": company, "from_date": "2020-01-01", "to_date": "2030-12-31"})

	def test_all_pack_reports_execute(self):
		filters = self._filters()
		for key in REPORT_SPECS:
			result = run_report(key, filters)
			columns, data = result[0], result[1]
			self.assertIsInstance(columns, list)
			self.assertIsInstance(data, list)


class TestWorldClassDocTypesExist(FrappeTestCase):
	EXPECTED = [
		"Healthcare Icd10 Code",
		"Healthcare Lab Test Panel",
		"Healthcare Imaging Modality",
		"Healthcare Prior Authorization",
		"Healthcare Claim Remittance",
		"Healthcare Patient Merge Log",
		"Healthcare Phi Access Log",
		"Healthcare Nursing Observation Chart",
		"Healthcare Medication Administration Record",
		"Healthcare Ward Requisition",
		"Healthcare Drug Interaction Rule",
	]

	def test_doctypes_installed(self):
		for dt in self.EXPECTED:
			self.assertTrue(frappe.db.exists("DocType", dt), msg=dt)
