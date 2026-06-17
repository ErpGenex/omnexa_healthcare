# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HealthcareMedicationRequest(Document):
	def validate(self):
		if self.docstatus == 0:
			self.status = self.status or "Draft"
		elif self.docstatus == 1 and not self.signed_on:
			self.status = "Signed"

	def on_submit(self):
		self.status = "Signed"
		self.signed_on = self.signed_on or now_datetime()
		self.signed_by = self.signed_by or frappe.session.user

	def on_cancel(self):
		self.status = "Cancelled"
