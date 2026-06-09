# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcarePreOpChecklist(Document):
	def validate(self):
		if self.who_checklist_complete:
			self.status = "Complete"
		elif self.site_marked and self.consent_signed and self.antibiotics_given:
			self.who_checklist_complete = 1
			self.status = "Complete"

	def before_save(self):
		if self.status == "Complete" and not (self.site_marked and self.consent_signed):
			frappe.throw(_("Site marked and consent signed are required for WHO checklist completion."))
