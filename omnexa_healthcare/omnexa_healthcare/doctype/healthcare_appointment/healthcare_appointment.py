# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareAppointment(Document):
	def validate(self):
		self._validate_required_context()
		self._validate_branch_company_match()
		self._validate_patient_context()
		self._validate_encounter_link()
		self._validate_service_unit_assignment()

	def _validate_required_context(self):
		if not self.patient:
			frappe.throw(_("Patient is mandatory for appointment."), title=_("Patient"))
		if not self.service_unit:
			frappe.throw(_("Service Unit is mandatory for appointment."), title=_("Service Unit"))

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_patient_context(self):
		if not self.patient:
			return
		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch", "active"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if not pdata.active:
			frappe.throw(_("Inactive patient records cannot receive new appointments."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(
				_("Patient must belong to the same company and branch as the appointment."),
				title=_("Patient"),
			)

	def _validate_encounter_link(self):
		if not self.encounter:
			return
		row = frappe.db.get_value(
			"Healthcare Encounter",
			self.encounter,
			["patient", "appointment", "company", "branch"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Encounter does not exist."), title=_("Encounter"))
		if row.patient != self.patient:
			frappe.throw(_("Encounter patient must match appointment patient."), title=_("Encounter"))
		if row.company != self.company or row.branch != self.branch:
			frappe.throw(_("Encounter must belong to the same company and branch."), title=_("Encounter"))
		if row.appointment and row.appointment != self.name:
			frappe.throw(_("Encounter is linked to a different appointment."), title=_("Encounter"))

	def _validate_service_unit_assignment(self):
		unit_data = frappe.db.get_value(
			"Healthcare Service Unit",
			self.service_unit,
			["company", "branch", "status"],
			as_dict=True,
		)
		if not unit_data:
			frappe.throw(_("Service Unit does not exist."), title=_("Service Unit"))
		if unit_data.company != self.company or unit_data.branch != self.branch:
			frappe.throw(_("Service Unit must belong to same company and branch."), title=_("Service Unit"))
		if unit_data.status != "Active":
			frappe.throw(_("Inactive units cannot accept appointments."), title=_("Service Unit"))
