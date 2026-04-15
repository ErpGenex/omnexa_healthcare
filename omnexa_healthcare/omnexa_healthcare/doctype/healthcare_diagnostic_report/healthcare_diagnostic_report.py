# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareDiagnosticReport(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_encounter()
		self._validate_service_request()
		self._validate_findings()

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
			frappe.throw(_("Inactive patient cannot receive diagnostic reports."), title=_("Patient"))

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
			frappe.throw(_("Encounter patient must match report patient."), title=_("Encounter"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Encounter must belong to the same company and branch."), title=_("Encounter"))

	def _validate_service_request(self):
		if not self.based_on_service_request:
			return
		row = frappe.db.get_value(
			"Healthcare Service Request",
			self.based_on_service_request,
			["patient", "company", "branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Service Request does not exist."), title=_("Service Request"))
		if row.patient != self.patient:
			frappe.throw(_("Service Request patient must match report patient."), title=_("Service Request"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Service Request must belong to the same company and branch."), title=_("Service Request"))

	def _validate_findings(self):
		for row in self.get("findings") or []:
			if not row.get("linked_observation") and not row.get("finding_narrative"):
				frappe.throw(
					_("Each finding row needs a linked observation or narrative."),
					title=_("Findings"),
				)
			obs = row.get("linked_observation")
			if not obs:
				continue
			odata = frappe.db.get_value(
				"Healthcare Observation",
				obs,
				["patient", "company", "branch"],
				as_dict=True,
			)
			if not odata:
				frappe.throw(_("Linked observation {0} does not exist.").format(obs), title=_("Findings"))
			if odata.patient != self.patient:
				frappe.throw(_("Linked observation must belong to the same patient."), title=_("Findings"))
			if odata.company != self.company or odata.branch != self.branch:
				frappe.throw(_("Linked observation must belong to the same company and branch."), title=_("Findings"))
