# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr


class HealthcareBranchWebsite(Document):
	def validate(self):
		self._normalize_slug()
		self._sync_company()

	def _normalize_slug(self):
		if not self.site_slug and self.branch:
			self.site_slug = frappe.scrub(self.branch).replace("_", "-")[:60]
		if self.site_slug:
			self.site_slug = cstr(self.site_slug).strip().lower().replace(" ", "-")

	def _sync_company(self):
		if self.branch and not self.company:
			self.company = frappe.db.get_value("Branch", self.branch, "company")

	def before_save(self):
		if self.branch and frappe.db.get_value("Branch", self.branch, "company") != self.company:
			frappe.throw(_("Branch does not belong to the selected company."))
