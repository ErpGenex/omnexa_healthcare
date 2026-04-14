# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareServiceUnit(Document):
	def validate(self):
		self.unit_code = (self.unit_code or "").strip().upper()
		self._validate_branch_company_match()
		self._validate_department_consistency()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Unit cannot belong to different company than branch."), title=_("Branch"))

	def _validate_department_consistency(self):
		if not self.department:
			return
		department_data = frappe.db.get_value(
			"Healthcare Department", self.department, ["company", "branch"], as_dict=True
		)
		if not department_data:
			frappe.throw(_("Department does not exist."), title=_("Department"))
		if department_data.company != self.company or department_data.branch != self.branch:
			frappe.throw(_("Department must belong to same company and branch."), title=_("Department"))
