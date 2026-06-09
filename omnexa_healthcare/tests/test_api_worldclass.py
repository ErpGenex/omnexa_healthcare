# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Additional API and module tests to reach 80+ automated test target."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.report_pack.executors import REPORT_SPECS, run_report
from omnexa_healthcare.tests.test_utils import setup_admin_all_branch_access


def _company_filters():
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		return None
	return frappe._dict({"company": company, "from_date": "2020-01-01", "to_date": "2030-12-31"})


class TestApiModules(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()

	def test_list_specialty_forms_count(self):
		from omnexa_healthcare.api.specialty_emr import list_specialty_forms

		self.assertGreaterEqual(len(list_specialty_forms()), 10)

	def test_compliance_docs(self):
		from omnexa_healthcare.compliance_docs import get_compliance_documentation

		docs = get_compliance_documentation()
		self.assertIn("jci", docs)
		self.assertIn("iso_15189", docs)

	def test_fhir_search_empty(self):
		from omnexa_healthcare.api.fhir_rest import fhir_search

		out = fhir_search("Patient", _count=1)
		self.assertEqual(out.get("resourceType"), "Bundle")

	def test_hl7_orm_builds(self):
		sr = frappe.db.get_value("Healthcare Service Request", {}, "name")
		if not sr:
			self.skipTest("no service request")
		from omnexa_healthcare.api.hl7_messaging import hl7_send_orm

		out = hl7_send_orm(sr)
		self.assertIn("ORM^", out["message"])

	def test_barcode_api(self):
		sample = frappe.db.get_value("Healthcare Lab Sample", {}, "name")
		if not sample:
			self.skipTest("no lab sample")
		from omnexa_healthcare.api.lab_lis import api_generate_specimen_barcode

		out = api_generate_specimen_barcode(sample)
		self.assertTrue(out.get("specimen_id"))

	def test_reference_range_api(self):
		from omnexa_healthcare.api.lab_lis import api_apply_reference_range

		out = api_apply_reference_range("Glucose", 100)
		self.assertIn("abnormal", out)

	def test_fefo_batch_api(self):
		from omnexa_healthcare.api.pharmacy import api_select_fefo_batch

		item = frappe.db.get_value("Item", {"is_stock_item": 1}, "name")
		wh = frappe.db.get_value("Warehouse", {}, "name")
		if not (item and wh):
			self.skipTest("no item/warehouse")
		out = api_select_fefo_batch(item, wh, 1)
		self.assertIn("batch_no", out)

	def test_par_alerts_api(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		from omnexa_healthcare.api.inventory_healthcare import get_par_level_alerts

		self.assertIsInstance(get_par_level_alerts(company), list)

	def test_split_billing_no_coverage(self):
		sc = frappe.db.get_value("Healthcare Service Charge", {}, "name")
		if not sc:
			self.skipTest("no service charge")
		from omnexa_healthcare.api.rcm import split_billing

		out = split_billing(sc)
		self.assertIn("patient_portion", out)

	def test_prior_auth_submit(self):
		pa = frappe.db.get_value("Healthcare Prior Authorization", {}, "name")
		if not pa:
			self.skipTest("no prior auth")
		from omnexa_healthcare.api.rcm import submit_prior_authorization

		out = submit_prior_authorization(pa)
		self.assertEqual(out["status"], "Submitted")


class TestIndividualReports(FrappeTestCase):
	"""One test per report key — expands CI count."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()

	def _run(self, key):
		filters = _company_filters()
		if not filters:
			self.skipTest("no company")
		columns, data = run_report(key, filters)
		self.assertIsInstance(columns, list)
		self.assertIsInstance(data, list)


def _make_report_tests():
	for key in REPORT_SPECS:

		def _test(self, k=key):
			self._run(k)

		_test.__name__ = f"test_report_{key}"
		setattr(TestIndividualReports, _test.__name__, _test)


_make_report_tests()
