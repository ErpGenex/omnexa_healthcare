# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareAppointment(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_service_unit_assignment()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_service_unit_assignment(self):
		unit_data = frappe.db.get_value(
			"Healthcare Service Unit",
			self.service_unit,
			["company", "branch", "status"],
			as_dict=True,
		)
		if not unit_data:
			frappe.throw(_("Service Unit does not exist."), title=_("Service Unit"))
		if unit_data.company != self.company or unit_data.branch != self.branch:
			frappe.throw(_("Service Unit must belong to same company and branch."), title=_("Service Unit"))
		if unit_data.status != "Active":
			frappe.throw(_("Inactive units cannot accept appointments."), title=_("Service Unit"))
