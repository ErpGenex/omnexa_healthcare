# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareBed(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_service_unit()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Company"))

	def _validate_service_unit(self):
		row = frappe.db.get_value(
			"Healthcare Service Unit",
			self.service_unit,
			["company", "branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Service unit does not exist."), title=_("Service Unit"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Service unit must belong to the same company and branch."), title=_("Service Unit"))

	def on_trash(self):
		if frappe.db.exists("Healthcare Admission", {"bed": self.name, "status": "Admitted"}):
			frappe.throw(_("Cannot delete a bed that has an active admission."), title=_("Bed"))
