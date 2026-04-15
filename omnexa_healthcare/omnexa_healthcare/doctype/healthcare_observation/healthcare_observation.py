# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


LAB_PROFILES = frozenset({"lab_glucose", "lab_hemoglobin"})


class HealthcareObservation(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_encounter()
		self._validate_category_profile()
		self._validate_blood_pressure()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_patient(self):
		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch", "active"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(_("Patient must belong to the same company and branch."), title=_("Patient"))
		if not pdata.active:
			frappe.throw(_("Inactive patient cannot receive new observations."), title=_("Patient"))

	def _validate_encounter(self):
		if not self.encounter:
			return
		row = frappe.db.get_value(
			"Healthcare Encounter",
			self.encounter,
			["patient", "company", "branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Encounter does not exist."), title=_("Encounter"))
		if row.patient != self.patient:
			frappe.throw(_("Encounter patient must match observation patient."), title=_("Encounter"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Encounter must belong to the same company and branch."), title=_("Encounter"))

	def _validate_category_profile(self):
		if self.observation_profile in LAB_PROFILES and self.category != "laboratory":
			frappe.throw(
				_("Laboratory result profiles require category laboratory."),
				title=_("Observation"),
			)

	def _validate_blood_pressure(self):
		if self.observation_profile != "blood_pressure":
			return
		if self.value_secondary is None:
			frappe.throw(_("Diastolic value is required for blood pressure."), title=_("Blood pressure"))
