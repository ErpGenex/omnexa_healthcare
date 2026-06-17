# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.i18n.healthcare_i18n_catalog import JOURNEY_AR, translate_to_ar
from omnexa_healthcare.i18n.sync_healthcare_translations import (
	build_translation_maps,
	collect_healthcare_strings,
)


class TestHealthcareI18n(unittest.TestCase):
	def test_workspace_sections_translated(self):
		self.assertEqual(translate_to_ar("📊 Dashboards & Portals"), "📊 لوحات المعلومات والبوابات")
		self.assertEqual(translate_to_ar("👤 MPI & Patient Access"), "👤 سجل المرضى والوصول")
		self.assertEqual(translate_to_ar("🌐 Omnexa Journey Experience"), "🌐 تجربة Omnexa Journey")

	def test_journey_ui_translated(self):
		self.assertEqual(translate_to_ar("Reception Desk"), "مكتب الاستقبال")
		self.assertEqual(translate_to_ar("Choose Clinic"), "اختيار العيادة")
		self.assertEqual(translate_to_ar("Confirm & Issue Token"), "تأكيد وإصدار التذكرة")
		self.assertEqual(translate_to_ar("Healthcare Demo Hub"), "مركز تجربة الرعاية الصحية")

	def test_patient_first_terminology(self):
		self.assertEqual(translate_to_ar("Customer"), "مريض")
		self.assertEqual(translate_to_ar("Healthcare Patient"), "مريض")

	def test_translation_coverage(self):
		strings = collect_healthcare_strings()
		ar_rows, _, stats = build_translation_maps()
		self.assertGreaterEqual(len(ar_rows), len(strings))
		journey_missing = [k for k in JOURNEY_AR if ar_rows.get(k) == k]
		self.assertEqual(journey_missing, [], f"Journey UI untranslated: {journey_missing[:5]}")
		# Codes (MRN, ICU, blood types) may remain unchanged.
		self.assertLessEqual(stats["ar_untranslated"], 700)
		untranslated = [s for s in strings if ar_rows.get(s) == s]
		for code in ("MRN", "ICU", "A+", "HL7", "LOINC"):
			self.assertIn(code, untranslated)

	def test_ar_csv_exists(self):
		from pathlib import Path

		path = Path(frappe.get_app_path("omnexa_healthcare")) / "translations" / "ar.csv"
		self.assertTrue(path.exists())
		lines = path.read_text(encoding="utf-8").strip().splitlines()
		self.assertGreater(len(lines), 500)
