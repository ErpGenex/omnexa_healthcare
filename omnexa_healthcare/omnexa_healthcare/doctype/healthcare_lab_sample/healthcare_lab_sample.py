# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareLabSample(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_service_request()

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

	def _validate_service_request(self):
		if not self.service_request:
			return
		row = frappe.db.get_value(
			"Healthcare Service Request",
			self.service_request,
			["patient", "company", "branch"],
			as_dict=True,
		)
		if not row or row.patient != self.patient:
			frappe.throw(_("Service request patient must match."), title=_("Service Request"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Service request must belong to the same company and branch."), title=_("Service Request"))
