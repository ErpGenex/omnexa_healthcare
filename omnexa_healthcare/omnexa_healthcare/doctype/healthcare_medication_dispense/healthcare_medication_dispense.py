# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HealthcareMedicationDispense(Document):
	def validate(self):
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_encounter()
		self._validate_medication_statement()
		self._validate_item()
		self._validate_warehouse()
		if self.status == "dispensed" and not self.dispensed_datetime:
			self.dispensed_datetime = now_datetime()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Company"))

	def _validate_patient(self):
		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(_("Patient must belong to the same company and branch."), title=_("Patient"))

	def _validate_encounter(self):
		if not self.encounter:
			return
		row = frappe.db.get_value("Healthcare Encounter", self.encounter, ["patient"], as_dict=True)
		if not row or row.patient != self.patient:
			frappe.throw(_("Encounter patient must match."), title=_("Encounter"))

	def _validate_medication_statement(self):
		if not self.medication_statement:
			return
		row = frappe.db.get_value(
			"Healthcare Medication Statement",
			self.medication_statement,
			["patient", "company", "branch"],
			as_dict=True,
		)
		if not row or row.patient != self.patient:
			frappe.throw(_("Medication statement patient must match."), title=_("Medication"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Medication statement must belong to the same company and branch."), title=_("Medication"))

	def _validate_item(self):
		it = frappe.db.get_value(
			"Item", self.item, ["company", "disabled", "is_stock_item"], as_dict=True
		)
		if not it:
			frappe.throw(_("Item does not exist."), title=_("Item"))
		if it.company != self.company:
			frappe.throw(_("Item belongs to a different company."), title=_("Item"))
		if it.disabled:
			frappe.throw(_("Item is disabled."), title=_("Item"))
		if self.warehouse and not it.is_stock_item:
			frappe.throw(
				_("Only stock-tracked items can be dispensed from a warehouse."),
				title=_("Item"),
			)

	def _validate_warehouse(self):
		if not self.warehouse:
			return
		wc = frappe.db.get_value("Warehouse", self.warehouse, "company")
		if wc != self.company:
			frappe.throw(_("Warehouse belongs to a different company."), title=_("Warehouse"))
