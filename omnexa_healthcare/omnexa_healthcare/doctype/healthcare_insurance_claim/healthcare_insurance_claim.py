# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HealthcareInsuranceClaim(Document):
	def validate(self):
		if flt(self.approved_amount) > flt(self.claim_amount):
			frappe.throw(_("Approved amount cannot exceed claim amount."), title=_("Insurance Claim"))

	def submit_claim(self):
		if self.status != "Draft":
			frappe.throw(_("Only draft claims can be submitted."))
		self.status = "Submitted"
		self.save()

	def approve_claim(self, approved_amount: float | None = None):
		if self.status not in ("Submitted", "Draft"):
			frappe.throw(_("Claim cannot be approved from status {0}.").format(self.status))
		self.approved_amount = flt(approved_amount) if approved_amount is not None else flt(self.claim_amount)
		self.status = "Approved"
		self.save()

	def mark_paid(self):
		self.status = "Paid"
		self.save()
