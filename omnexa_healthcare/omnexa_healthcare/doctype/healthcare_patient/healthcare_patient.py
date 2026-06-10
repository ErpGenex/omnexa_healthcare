# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcarePatient(Document):
	def validate(self):
		from omnexa_healthcare.patient_billing import ensure_patient_billing_account, ensure_patient_identifiers

		ensure_patient_identifiers(self)
		self._set_full_name()
		self._validate_branch_company_match()
		self._validate_managing_facility()
		ensure_patient_billing_account(self)
		self._validate_billing_customer()
		self._validate_identifiers()
		self._validate_telecom()
		self._validate_deceased()

	def _set_full_name(self):
		parts = [
			(self.name_prefix or "").strip(),
			(self.given_name or "").strip(),
			(self.middle_name or "").strip(),
			(self.family_name or "").strip(),
			(self.name_suffix or "").strip(),
		]
		self.full_name = " ".join(p for p in parts if p).strip()
		if not self.full_name:
			frappe.throw(_("Full display name could not be built from name parts."), title=_("Name"))

	def _validate_branch_company_match(self):
		if not self.branch:
			return
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_managing_facility(self):
		if not self.managing_facility:
			return
		f = frappe.db.get_value(
			"Healthcare Facility Profile",
			self.managing_facility,
			["company", "branch"],
			as_dict=True,
		)
		if not f:
			frappe.throw(_("Managing facility does not exist."), title=_("Facility"))
		if f.company != self.company or f.branch != self.branch:
			frappe.throw(
				_("Managing facility must belong to the same company and branch."),
				title=_("Facility"),
			)

	def _validate_billing_customer(self):
		if not self.billing_customer:
			return
		c_company = frappe.db.get_value("Customer", self.billing_customer, "company")
		if not c_company:
			frappe.throw(_("Billing account does not exist."), title=_("Patient"))
		if c_company != self.company:
			frappe.throw(_("Billing account must belong to the same company."), title=_("Patient"))

	def _validate_identifiers(self):
		if not self.identifiers:
			frappe.throw(_("At least one identifier is required (e.g. MRN or national ID)."), title=_("Identifiers"))

		for row in self.identifiers:
			if row.is_primary_mrn and row.identifier_type != "MRN":
				frappe.throw(
					_("Primary MRN applies only to rows with identifier type MRN."),
					title=_("Identifiers"),
				)

		mrn_rows = [d for d in self.identifiers if d.identifier_type == "MRN" and (d.value or "").strip()]
		if mrn_rows:
			primary_mrns = [d for d in mrn_rows if d.is_primary_mrn]
			if len(primary_mrns) != 1:
				frappe.throw(
					_("When an MRN is recorded, exactly one row must be marked as Primary MRN."),
					title=_("MRN"),
				)

		seen = set()
		for row in self.identifiers:
			key = (row.identifier_type, (row.value or "").strip().lower())
			if not row.value or not row.value.strip():
				frappe.throw(_("Identifier value is required on each row."), title=_("Identifiers"))
			if key in seen:
				frappe.throw(
					_("Duplicate identifier type and value combination."),
					title=_("Identifiers"),
				)
			seen.add(key)

	def _validate_telecom(self):
		for row in self.telecom or []:
			if not (row.value or "").strip():
				frappe.throw(_("Telecom value is required on each row."), title=_("Telecom"))

	def _validate_deceased(self):
		if self.deceased and not self.deceased_datetime:
			frappe.throw(_("Deceased date/time is required when deceased is checked."), title=_("Deceased"))
		if not self.deceased:
			self.deceased_datetime = None
