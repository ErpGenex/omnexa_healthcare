# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

import frappe

from omnexa_healthcare.api.follow_up_plan import (
	create_follow_up_plan,
	get_follow_up_templates,
	get_patient_follow_up_plans,
	list_multi_visit_specialties,
)
from omnexa_healthcare.api.patient_journey import get_patient_journey
from omnexa_healthcare.follow_up_templates import MULTI_VISIT_MODULE_CODES


class TestFollowUpPlan(unittest.TestCase):
	def test_multi_visit_specialties_listed(self):
		rows = list_multi_visit_specialties()
		self.assertGreaterEqual(len(rows), 10)
		codes = {r["module_code"] for r in rows}
		self.assertIn("orthopedics", codes)
		self.assertIn("gynecology", codes)

	def test_antenatal_template_has_eight_visits(self):
		spec = frappe.db.get_value("Healthcare Specialty Module", "gynecology", "specialty")
		if not spec:
			self.skipTest("Gynecology specialty module not seeded")
		tpl = get_follow_up_templates(spec, "antenatal")
		self.assertEqual(tpl["plan_type"], "antenatal")
		self.assertGreaterEqual(len(tpl["visits"]), 8)

	def test_create_orthopedic_follow_up_plan(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		spec = frappe.db.get_value("Healthcare Specialty Module", "orthopedics", "specialty")
		if not (patient and spec):
			self.skipTest("No patient or orthopedics module")
		out = create_follow_up_plan(patient=patient, specialty=spec, plan_type="rehabilitation")
		self.assertTrue(out.get("name"))
		self.assertGreaterEqual(out.get("visit_count", 0), 4)
		plans = get_patient_follow_up_plans(patient, specialty=spec)
		self.assertTrue(any(p["name"] == out["name"] for p in plans))

	def test_patient_journey_includes_follow_up_plans(self):
		patient = frappe.db.get_value("Healthcare Patient", {}, "name")
		if not patient:
			self.skipTest("No patient")
		journey = get_patient_journey(patient)
		self.assertEqual(len(journey["steps"]), 10)
		self.assertIn("follow_up_plans", journey)

	def test_all_template_modules_registered(self):
		self.assertGreaterEqual(len(MULTI_VISIT_MODULE_CODES), 12)

	def test_every_plan_type_has_template(self):
		from omnexa_healthcare.follow_up_templates import FOLLOW_UP_PLAN_TEMPLATES

		missing = []
		for code, cfg in FOLLOW_UP_PLAN_TEMPLATES.items():
			if not cfg.get("supports_multi_visit"):
				continue
			templates = cfg.get("templates") or {}
			for pt in cfg.get("plan_types") or []:
				if pt not in templates:
					missing.append(f"{code}:{pt}")
		self.assertEqual(missing, [], f"Missing follow-up templates: {missing}")

	def test_cardiology_post_op_template(self):
		spec = frappe.db.get_value("Healthcare Specialty Module", "cardiology", "specialty")
		if not spec:
			self.skipTest("Cardiology module not seeded")
		tpl = get_follow_up_templates(spec, "post_op")
		self.assertEqual(tpl["plan_type"], "post_op")
		self.assertGreaterEqual(len(tpl["visits"]), 2)

	def test_physiotherapy_rehabilitation_template(self):
		spec = frappe.db.get_value("Healthcare Specialty Module", "physiotherapy", "specialty")
		if not spec:
			self.skipTest("Physiotherapy module not seeded")
		tpl = get_follow_up_templates(spec, "rehabilitation")
		self.assertEqual(tpl["plan_type"], "rehabilitation")
		self.assertGreaterEqual(len(tpl["visits"]), 3)
