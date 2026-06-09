# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareErVisit(Document):
	def validate(self):
		if self.esi_level and int(self.esi_level) not in range(1, 6):
			frappe.throw(_("ESI level must be between 1 and 5."), title=_("ER Triage"))
