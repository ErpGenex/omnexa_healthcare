# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareDentalChartEntry(Document):
	def validate(self):
		if self.patient and self.company:
			patient_company = frappe.db.get_value("Healthcare Patient", self.patient, "company")
			if patient_company and patient_company != self.company:
				frappe.throw(_("Patient must belong to the same company."), title=_("Patient"))
