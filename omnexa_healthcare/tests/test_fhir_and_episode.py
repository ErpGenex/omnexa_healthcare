import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.api.dispensing import create_stock_entry_from_medication_dispense
from omnexa_healthcare.api.fhir_export import (
	get_fhir_allergy_intolerance,
	get_fhir_clinical_condition,
	get_fhir_diagnostic_report,
	get_fhir_encounter,
	get_fhir_episode_of_care,
	get_fhir_patient,
	get_fhir_patient_summary_ips_bundle,
	get_fhir_service_request,
)
from omnexa_healthcare.tests.test_utils import ensure_currency_and_country, ensure_company_stock_gl, make_test_branch, setup_admin_all_branch_access


class TestFhirExportAndEpisode(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		setup_admin_all_branch_access()
		ensure_currency_and_country()

	def _make_company(self, label):
		abbr = f"FE{label}{frappe.generate_hash(length=2).upper()}"
		doc = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"FHIR Co {label}",
				"abbr": abbr,
				"default_currency": "EGP",
				"country": "Egypt",
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_branch(self, company, code):
		return make_test_branch(company, code)

	def _make_patient(self, company, branch):
		return frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company,
				"branch": branch,
				"given_name": "Fhir",
				"family_name": "Test",
				"gender": "male",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": f"MRN-{frappe.generate_hash(length=6)}",
						"is_primary_mrn": 1,
					}
				],
			}
		).insert(ignore_permissions=True)

	def test_fhir_patient_export_shape(self):
		company = self._make_company("A")
		branch = self._make_branch(company, "FA")
		patient = self._make_patient(company, branch)
		data = get_fhir_patient(patient.name)
		self.assertEqual(data["resourceType"], "Patient")
		self.assertEqual(data["id"], patient.name)
		self.assertIn("identifier", data)

	def test_encounter_linked_to_episode_fhir(self):
		company = self._make_company("B")
		branch = self._make_branch(company, "FB")
		patient = self._make_patient(company, branch)
		episode = frappe.get_doc(
			{
				"doctype": "Healthcare Episode Of Care",
				"naming_series": "EOC-.#####",
				"episode_title": "Diabetes follow-up",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"episode_type": "chronic_disease",
				"status": "active",
				"period_start": "2026-01-01",
			}
		).insert(ignore_permissions=True)
		enc = frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": patient.name,
				"episode_of_care": episode.name,
				"company": company,
				"branch": branch,
				"encounter_class": "ambulatory",
				"encounter_type": "OPD",
				"status": "finished",
				"period_start": "2026-06-01 10:00:00",
				"period_end": "2026-06-01 10:30:00",
			}
		).insert(ignore_permissions=True)
		data = get_fhir_encounter(enc.name)
		self.assertEqual(data["resourceType"], "Encounter")
		self.assertTrue(any("EpisodeOfCare" in x.get("reference", "") for x in data.get("episodeOfCare", [])))

	def test_fhir_episode_export_shape(self):
		company = self._make_company("C")
		branch = self._make_branch(company, "FC")
		patient = self._make_patient(company, branch)
		episode = frappe.get_doc(
			{
				"doctype": "Healthcare Episode Of Care",
				"naming_series": "EOC-.#####",
				"episode_title": "Rehab program",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"episode_type": "rehabilitation",
				"status": "planned",
				"period_start": "2026-03-01",
			}
		).insert(ignore_permissions=True)
		data = get_fhir_episode_of_care(episode.name)
		self.assertEqual(data["resourceType"], "EpisodeOfCare")
		self.assertEqual(data["status"], "planned")

	def test_ips_document_bundle_and_condition_allergy_fhir(self):
		company = self._make_company("E")
		branch = self._make_branch(company, "FE")
		patient = self._make_patient(company, branch)
		cond = frappe.get_doc(
			{
				"doctype": "Healthcare Clinical Condition",
				"naming_series": "CC-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"category": "problem-list-item",
				"icd10_code": "E11",
				"clinical_description": "Type 2 diabetes mellitus",
				"clinical_status": "active",
				"verification_status": "confirmed",
			}
		).insert(ignore_permissions=True)
		alg = frappe.get_doc(
			{
				"doctype": "Healthcare Allergy Intolerance",
				"naming_series": "ALG-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"allergy_type": "allergy",
				"category": "medication",
				"criticality": "high",
				"substance_text": "Penicillin",
				"reaction_manifestation": "Urticaria",
				"clinical_status": "active",
				"verification_status": "confirmed",
			}
		).insert(ignore_permissions=True)

		c_res = get_fhir_clinical_condition(cond.name)
		self.assertEqual(c_res["resourceType"], "Condition")
		self.assertEqual(c_res["code"]["coding"][0]["code"], "E11")

		a_res = get_fhir_allergy_intolerance(alg.name)
		self.assertEqual(a_res["resourceType"], "AllergyIntolerance")
		self.assertEqual(a_res["code"]["text"], "Penicillin")

		bundle = get_fhir_patient_summary_ips_bundle(patient.name)
		self.assertEqual(bundle["resourceType"], "Bundle")
		self.assertEqual(bundle["type"], "document")
		self.assertEqual(bundle["entry"][0]["resource"]["resourceType"], "Composition")
		self.assertEqual(
			bundle["entry"][0]["resource"]["type"]["coding"][0]["code"],
			"60591-5",
		)

	def test_ips_bundle_medications_immunizations_vitals_loinc_sections(self):
		company = self._make_company("G")
		branch = self._make_branch(company, "FG")
		patient = self._make_patient(company, branch)
		frappe.get_doc(
			{
				"doctype": "Healthcare Medication Statement",
				"naming_series": "MED-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"status": "active",
				"medication_text": "Metformin 500 mg",
				"dosage_text": "Twice daily with meals",
				"category": "community",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Healthcare Immunization",
				"naming_series": "IMM-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"status": "completed",
				"occurrence_datetime": "2026-01-15 09:00:00",
				"vaccine_name": "COVID-19 mRNA vaccine",
				"cvx_code": "208",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Healthcare Observation",
				"naming_series": "OBS-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"observation_profile": "heart_rate",
				"status": "final",
				"value_primary": 72,
				"effective_datetime": "2026-06-01 08:00:00",
			}
		).insert(ignore_permissions=True)

		bundle = get_fhir_patient_summary_ips_bundle(patient.name)
		comp = bundle["entry"][0]["resource"]
		self.assertIn("author", comp)
		loinc_codes = []
		for sec in comp.get("section", []):
			for c in sec.get("code", {}).get("coding", []):
				code = c.get("code")
				if code:
					loinc_codes.append(code)
		self.assertIn("10160-0", loinc_codes)
		self.assertIn("11369-6", loinc_codes)
		self.assertIn("8716-3", loinc_codes)

	def test_ips_bundle_orders_diagnostics_loinc_30954_2(self):
		company = self._make_company("H")
		branch = self._make_branch(company, "FH")
		patient = self._make_patient(company, branch)
		sr = frappe.get_doc(
			{
				"doctype": "Healthcare Service Request",
				"naming_series": "SRQ-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"status": "active",
				"intent": "order",
				"request_category": "laboratory",
				"priority": "routine",
				"request_title": "CBC panel",
				"request_loinc": "58410-2",
				"authored_on": "2026-06-01 09:00:00",
			}
		).insert(ignore_permissions=True)
		lab_obs = frappe.get_doc(
			{
				"doctype": "Healthcare Observation",
				"naming_series": "OBS-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"category": "laboratory",
				"observation_profile": "lab_glucose",
				"status": "final",
				"value_primary": 95,
				"effective_datetime": "2026-06-01 10:00:00",
			}
		).insert(ignore_permissions=True)
		dgr = frappe.get_doc(
			{
				"doctype": "Healthcare Diagnostic Report",
				"naming_series": "DGR-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"based_on_service_request": sr.name,
				"report_category": "laboratory",
				"report_title": "Glucose result",
				"report_loinc": "2345-7",
				"status": "final",
				"effective_datetime": "2026-06-01 11:00:00",
				"conclusion": "Within reference range.",
				"findings": [{"linked_observation": lab_obs.name}],
			}
		).insert(ignore_permissions=True)

		sr_fhir = get_fhir_service_request(sr.name)
		self.assertEqual(sr_fhir["resourceType"], "ServiceRequest")
		self.assertEqual(sr_fhir["code"]["coding"][0]["code"], "58410-2")

		dr_fhir = get_fhir_diagnostic_report(dgr.name)
		self.assertEqual(dr_fhir["resourceType"], "DiagnosticReport")
		self.assertTrue(any("Observation" in r.get("reference", "") for r in dr_fhir.get("result", [])))

		bundle = get_fhir_patient_summary_ips_bundle(patient.name)
		comp = bundle["entry"][0]["resource"]
		loinc_codes = []
		for sec in comp.get("section", []):
			for c in sec.get("code", {}).get("coding", []):
				code = c.get("code")
				if code:
					loinc_codes.append(code)
		self.assertIn("30954-2", loinc_codes)

	def _ensure_uom_unit(self):
		if frappe.db.exists("UOM", "Unit"):
			return "Unit"
		frappe.get_doc({"doctype": "UOM", "uom_name": "Unit"}).insert(ignore_permissions=True)
		return "Unit"

	def test_medication_dispense_creates_material_issue_stock_entry(self):
		company = self._make_company("RX")
		branch = self._make_branch(company, "PH")
		patient = self._make_patient(company, branch)
		uom = self._ensure_uom_unit()
		code = f"TAB-{frappe.generate_hash(length=4)}"
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": "Test drug",
				"company": company,
				"stock_uom": uom,
				"is_stock_item": 1,
				"current_stock_qty": 50,
			}
		).insert(ignore_permissions=True)
		wh = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": f"Pharmacy {code}",
				"warehouse_code": f"W{frappe.generate_hash(length=3)}",
				"company": company,
			}
		).insert(ignore_permissions=True)
		ensure_company_stock_gl(company, wh.name)
		md = frappe.get_doc(
			{
				"doctype": "Healthcare Medication Dispense",
				"naming_series": "MDP-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"item": item.name,
				"qty": 2,
				"warehouse": wh.name,
				"status": "draft",
			}
		).insert(ignore_permissions=True)
		out = create_stock_entry_from_medication_dispense(md.name)
		self.assertTrue(out.get("stock_entry"))
		se = frappe.get_doc("Stock Entry", out["stock_entry"])
		self.assertEqual(se.docstatus, 1)
		self.assertEqual(se.purpose, "Material Issue")
		self.assertEqual(
			frappe.db.get_value("Healthcare Medication Dispense", md.name, "status"),
			"dispensed",
		)
		self.assertEqual(frappe.db.get_value("Item", item.name, "current_stock_qty"), 48)

	def test_inpatient_admission_marks_bed_occupied_and_frees_on_discharge(self):
		company = self._make_company("IP")
		branch = self._make_branch(company, "IPW")
		patient = self._make_patient(company, branch)
		dept = frappe.get_doc(
			{
				"doctype": "Healthcare Department",
				"department_name": "Internal Med",
				"department_code": "IM",
				"company": company,
				"branch": branch,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		su = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"unit_name": "Ward A",
				"unit_code": "WA",
				"company": company,
				"branch": branch,
				"department": dept.name,
				"unit_type": "Ward",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		bed = frappe.get_doc(
			{
				"doctype": "Healthcare Bed",
				"naming_series": "BED-.#####",
				"bed_label": "1",
				"company": company,
				"branch": branch,
				"service_unit": su.name,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Healthcare Bed", bed.name, "status"), "Available")
		adm = frappe.get_doc(
			{
				"doctype": "Healthcare Admission",
				"naming_series": "ADM-.#####",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"status": "admitted",
				"bed": bed.name,
				"admission_datetime": "2026-06-01 08:00:00",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Healthcare Bed", bed.name, "status"), "Occupied")
		adm.status = "discharged"
		adm.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Healthcare Bed", bed.name, "status"), "Available")

	def test_encounter_rejected_when_episode_closed(self):
		company = self._make_company("D")
		branch = self._make_branch(company, "FD")
		patient = self._make_patient(company, branch)
		episode = frappe.get_doc(
			{
				"doctype": "Healthcare Episode Of Care",
				"naming_series": "EOC-.#####",
				"episode_title": "Closed path",
				"patient": patient.name,
				"company": company,
				"branch": branch,
				"episode_type": "other",
				"status": "finished",
				"period_start": "2026-01-01",
				"period_end": "2026-02-01",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Encounter",
					"naming_series": "ENC-.#####",
					"patient": patient.name,
					"episode_of_care": episode.name,
					"company": company,
					"branch": branch,
					"encounter_class": "ambulatory",
					"encounter_type": "OPD",
					"status": "planned",
					"period_start": "2026-06-10 09:00:00",
				}
			).insert(ignore_permissions=True)
