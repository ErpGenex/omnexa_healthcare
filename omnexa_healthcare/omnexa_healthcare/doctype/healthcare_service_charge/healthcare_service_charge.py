# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HealthcareServiceCharge(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient_and_customer()
		self._validate_encounter_admission()
		self._sync_line_amounts()
		if self.status == "Invoiced" and not self.sales_invoice:
			frappe.throw(_("Invoiced charges must reference a Sales Invoice."), title=_("Status"))

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Company"))

	def _validate_patient_and_customer(self):
		from omnexa_healthcare.patient_billing import ensure_patient_billing_account

		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch", "billing_customer"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(_("Patient must belong to the same company and branch."), title=_("Patient"))
		if not self.billing_customer:
			self.billing_customer = ensure_patient_billing_account(self.patient) or pdata.billing_customer
		if not self.billing_customer:
			frappe.throw(_("Patient billing account could not be resolved."), title=_("Patient"))
		c_company = frappe.db.get_value("Customer", self.billing_customer, "company")
		if c_company != self.company:
			frappe.throw(_("Billing account belongs to a different company."), title=_("Patient"))

	def _validate_encounter_admission(self):
		if self.encounter:
			p = frappe.db.get_value("Healthcare Encounter", self.encounter, "patient")
			if p != self.patient:
				frappe.throw(_("Encounter patient must match."), title=_("Encounter"))
		if self.admission:
			row = frappe.db.get_value(
				"Healthcare Admission",
				self.admission,
				["patient", "company", "branch"],
				as_dict=True,
			)
			if not row or row.patient != self.patient:
				frappe.throw(_("Admission patient must match."), title=_("Admission"))
			if row.company != self.company or row.branch != self.branch:
				frappe.throw(_("Admission must belong to the same company and branch."), title=_("Admission"))

	def _sync_line_amounts(self):
		for row in self.items or []:
			if row.item:
				it = frappe.get_cached_doc("Item", row.item)
				if it.company != self.company:
					frappe.throw(_("Row {0}: Item belongs to a different company.").format(row.idx), title=_("Item"))
				if not row.item_code:
					row.item_code = it.item_code
			gross = flt(row.qty) * flt(row.rate)
			discount = flt(row.patient_discount_amount) or (gross * flt(row.patient_discount_percent) / 100)
			row.amount = flt(gross - discount)
		from omnexa_healthcare.api.physician_compensation_engine import apply_line_compensation_preview

		apply_line_compensation_preview(self)
