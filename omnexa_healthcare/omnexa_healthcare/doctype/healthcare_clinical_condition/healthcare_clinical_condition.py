# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class HealthcareClinicalCondition(Document):
	def validate(self):
		if not self.recorded_date:
			self.recorded_date = today()
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_encounter()
		self._validate_episode()

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
			frappe.throw(
				_("Patient must belong to the same company and branch."),
				title=_("Patient"),
			)
		if not pdata.active:
			frappe.throw(_("Inactive patient cannot receive new conditions."), title=_("Patient"))

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
			frappe.throw(_("Encounter patient must match condition patient."), title=_("Encounter"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Encounter must belong to the same company and branch."), title=_("Encounter"))

	def _validate_episode(self):
		if not self.episode_of_care:
			return
		row = frappe.db.get_value(
			"Healthcare Episode Of Care",
			self.episode_of_care,
			["patient", "company", "branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Episode of Care does not exist."), title=_("Episode"))
		if row.patient != self.patient:
			frappe.throw(_("Episode patient must match condition patient."), title=_("Episode"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Episode must belong to the same company and branch."), title=_("Episode"))
