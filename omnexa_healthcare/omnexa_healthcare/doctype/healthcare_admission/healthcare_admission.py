# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HealthcareAdmission(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_episode_encounter()
		self._validate_admission_rules()
		if self.status == "discharged" and not self.discharge_datetime:
			self.discharge_datetime = now_datetime()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Company"))

	def _validate_patient(self):
		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(_("Patient must belong to the same company and branch."), title=_("Patient"))

	def _validate_episode_encounter(self):
		if self.episode_of_care:
			ep = frappe.db.get_value(
				"Healthcare Episode Of Care",
				self.episode_of_care,
				["patient"],
				as_dict=True,
			)
			if not ep or ep.patient != self.patient:
				frappe.throw(_("Episode patient must match admission patient."), title=_("Episode"))
		if self.encounter:
			en = frappe.db.get_value("Healthcare Encounter", self.encounter, ["patient"], as_dict=True)
			if not en or en.patient != self.patient:
				frappe.throw(_("Encounter patient must match admission patient."), title=_("Encounter"))

	def _validate_admission_rules(self):
		if not self.is_new():
			prev = frappe.db.get_value(
				"Healthcare Admission",
				self.name,
				["status", "bed"],
				as_dict=True,
			)
			if (
				prev
				and prev.get("status") == "admitted"
				and prev.get("bed")
				and self.bed
				and prev.get("bed") != self.bed
			):
				frappe.throw(_("Cannot change bed while admitted; discharge first."), title=_("Bed"))

		if self.status == "admitted":
			if not self.bed:
				frappe.throw(_("Bed is required for an admitted patient."), title=_("Bed"))
			pf = {"patient": self.patient, "status": "admitted"}
			if self.name:
				pf["name"] = ["!=", self.name]
			if frappe.db.exists("Healthcare Admission", pf):
				frappe.throw(
					_("This patient already has an active admission."),
					title=_("Admission"),
				)
			bf = {"bed": self.bed, "status": "admitted"}
			if self.name:
				bf["name"] = ["!=", self.name]
			if frappe.db.exists("Healthcare Admission", bf):
				frappe.throw(_("This bed already has an active admission."), title=_("Bed"))

			prev_status = (
				frappe.db.get_value("Healthcare Admission", self.name, "status") if self.name else None
			)
			prev_bed = frappe.db.get_value("Healthcare Admission", self.name, "bed") if self.name else None
			same_admitted_stay = (
				prev_status == "admitted" and prev_bed and prev_bed == self.bed and self.status == "admitted"
			)
			if not same_admitted_stay:
				bst = frappe.db.get_value("Healthcare Bed", self.bed, "status")
				if bst not in ("Available", "Reserved"):
					frappe.throw(_("Bed is not available for admission."), title=_("Bed"))

			bdoc = frappe.db.get_value(
				"Healthcare Bed",
				self.bed,
				["company", "branch"],
				as_dict=True,
			)
			if not bdoc or bdoc.company != self.company or bdoc.branch != self.branch:
				frappe.throw(_("Bed must belong to the same company and branch."), title=_("Bed"))

	def after_insert(self):
		self._sync_bed_status()

	def on_update(self):
		self._sync_bed_status()

	def _sync_bed_status(self):
		if self.status == "admitted" and self.bed:
			frappe.db.set_value("Healthcare Bed", self.bed, "status", "Occupied", update_modified=False)
		elif self.status in ("discharged", "cancelled") and self.bed:
			frappe.db.set_value("Healthcare Bed", self.bed, "status", "Available", update_modified=False)
