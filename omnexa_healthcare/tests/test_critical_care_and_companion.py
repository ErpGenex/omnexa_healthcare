# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare.api.critical_care import api_get_critical_care_board
from omnexa_healthcare.omnexa_healthcare.doctype.healthcare_critical_care_monitoring.healthcare_critical_care_monitoring import (
	compute_alert_level,
)


class TestCriticalCareAndCompanion(FrappeTestCase):
	def setUp(self):
		self.company = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
		if not self.company:
			self.skipTest("No company")
		self.branch = frappe.db.get_value("Branch", {"company": self.company}, "name")
		if not self.branch:
			self.skipTest("No branch")
		self._cleanup = []

	def tearDown(self):
		for dt, name in reversed(self._cleanup):
			if frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=1, ignore_permissions=True)

	def _track(self, dt: str, name: str) -> None:
		self._cleanup.append((dt, name))

	def _make_unit(self, code: str, unit_type: str, label: str) -> str:
		dept = frappe.db.get_value("Healthcare Department", {"branch": self.branch}, "name")
		if not dept:
			dept_doc = frappe.get_doc(
				{
					"doctype": "Healthcare Department",
					"department_name": f"Dept-{code}",
					"department_code": code[:6],
					"company": self.company,
					"branch": self.branch,
					"status": "Active",
				}
			).insert(ignore_permissions=True)
			dept = dept_doc.name
			self._track("Healthcare Department", dept)
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"unit_name": label,
				"unit_code": code,
				"company": self.company,
				"branch": self.branch,
				"department": dept,
				"unit_type": unit_type,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Service Unit", doc.name)
		return doc.name

	def _make_bed(self, unit: str, bed_type: str, label: str) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Bed",
				"bed_label": label,
				"company": self.company,
				"branch": self.branch,
				"service_unit": unit,
				"bed_type": bed_type,
				"status": "Available",
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Bed", doc.name)
		return doc.name

	def _make_patient(self, suffix: str) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"given_name": f"CC{suffix}",
				"family_name": "Test",
				"company": self.company,
				"branch": self.branch,
				"gender": "male",
				"date_of_birth": "1990-01-01",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": f"MRN-CC-{suffix}-{frappe.generate_hash(length=4)}",
						"is_primary_mrn": 1,
					}
				],
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Patient", doc.name)
		return doc.name

	def test_companion_bed_rejected_on_patient_admission(self):
		unit = self._make_unit("CMP-T", "Companion Ward", "Companion Test")
		bed = self._make_bed(unit, "Companion", "CMP-T-01")
		patient = self._make_patient("adm")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Healthcare Admission",
					"naming_series": "ADM-.#####",
					"patient": patient,
					"company": self.company,
					"branch": self.branch,
					"admission_class": "elective",
					"status": "admitted",
					"bed": bed,
					"admission_datetime": "2026-06-01 08:00:00",
				}
			).insert(ignore_permissions=True)

	def test_companion_stay_and_icu_monitoring(self):
		icu_unit = self._make_unit("ICU-T", "ICU", "ICU Test")
		cmp_unit = self._make_unit("CMP2-T", "Companion Ward", "Companion Lodging")
		ward_unit = self._make_unit("WRD-T", "Ward", "Ward Test")
		icu_bed = self._make_bed(icu_unit, "ICU", "ICU-T-01")
		cmp_bed = self._make_bed(cmp_unit, "Companion", "CMP-T-02")
		ipd_bed = self._make_bed(ward_unit, "General", "WRD-T-01")
		patient = self._make_patient("icu")
		admit = frappe.get_doc(
			{
				"doctype": "Healthcare Admission",
				"naming_series": "ADM-.#####",
				"patient": patient,
				"company": self.company,
				"branch": self.branch,
				"admission_class": "emergency",
				"status": "admitted",
				"bed": icu_bed,
				"admission_datetime": "2026-06-01 08:00:00",
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Admission", admit.name)

		mon = frappe.get_doc(
			{
				"doctype": "Healthcare Critical Care Monitoring",
				"patient": patient,
				"admission": admit.name,
				"bed": icu_bed,
				"care_unit": "ICU",
				"recorded_at": "2026-06-01 09:00:00",
				"heart_rate": 170,
				"spo2": 86,
				"company": self.company,
				"branch": self.branch,
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Critical Care Monitoring", mon.name)
		self.assertEqual(mon.alert_level, "Critical")

		board = api_get_critical_care_board(self.branch)
		self.assertTrue(any(row.admission == admit.name for row in board))

		ipd_patient = self._make_patient("ipd")
		ipd_admit = frappe.get_doc(
			{
				"doctype": "Healthcare Admission",
				"naming_series": "ADM-.#####",
				"patient": ipd_patient,
				"company": self.company,
				"branch": self.branch,
				"admission_class": "elective",
				"status": "admitted",
				"bed": ipd_bed,
				"admission_datetime": "2026-06-01 07:00:00",
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Admission", ipd_admit.name)

		stay = frappe.get_doc(
			{
				"doctype": "Healthcare Companion Stay",
				"patient": ipd_patient,
				"admission": ipd_admit.name,
				"companion_name": "Escort Test",
				"relationship": "Mother",
				"bed": cmp_bed,
				"check_in_datetime": "2026-06-01 20:00:00",
				"status": "active",
				"company": self.company,
				"branch": self.branch,
			}
		).insert(ignore_permissions=True)
		self._track("Healthcare Companion Stay", stay.name)
		self.assertEqual(frappe.db.get_value("Healthcare Bed", cmp_bed, "status"), "Occupied")

	def test_compute_alert_level_nicu(self):
		level = compute_alert_level(
			frappe._dict(care_unit="NICU", spo2=88, heart_rate=150, respiratory_rate=35)
		)
		self.assertIn(level, ("Warning", "Critical"))
