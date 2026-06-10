# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class HealthcareFollowUpPlan(Document):  # DocType: Healthcare Follow Up Plan
	def validate(self):
		if self.patient and self.company:
			patient_company = frappe.db.get_value("Healthcare Patient", self.patient, "company")
			if patient_company and patient_company != self.company:
				frappe.throw(_("Patient must belong to the same company."), title=_("Patient"))
		self._sync_visit_numbers()
		self._sync_dates_from_visits()

	def _sync_visit_numbers(self):
		for idx, row in enumerate(self.visits or [], start=1):
			row.visit_no = idx

	def _sync_dates_from_visits(self):
		dates = [getdate(row.planned_date) for row in (self.visits or []) if row.planned_date]
		if dates and not self.start_date:
			self.start_date = min(dates)
		if dates:
			self.expected_end_date = max(dates)
