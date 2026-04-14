# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareDepartment(Document):
	def validate(self):
		self.department_code = (self.department_code or "").strip().upper()
		self._validate_branch_company_match()
		self._validate_unique_department_code()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_unique_department_code(self):
		dupe = frappe.db.exists(
			"Healthcare Department",
			{"branch": self.branch, "department_code": self.department_code},
		)
		if dupe and (self.is_new() or dupe != self.name):
			frappe.throw(
				_("Department Code must be unique within the same branch."),
				title=_("Validation"),
			)
