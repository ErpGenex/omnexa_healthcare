# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareFacilityProfile(Document):
	def validate(self):
		self.facility_name = (self.facility_name or "").strip()
		self._validate_branch_company_match()

	def _validate_branch_company_match(self):
		if not self.branch:
			return
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))
