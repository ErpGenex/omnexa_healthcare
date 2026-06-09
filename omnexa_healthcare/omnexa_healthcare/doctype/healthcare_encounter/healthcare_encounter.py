# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class HealthcareEncounter(Document):
	def validate(self):
		self._sync_from_appointment()
		self._validate_diagnoses()
		self._validate_branch_company_match()
		self._validate_patient()
		self._validate_appointment_link()
		self._validate_episode_of_care()
		self._validate_single_encounter_per_appointment()
		self._validate_location_hierarchy()
		self._validate_period()

	def after_insert(self):
		self._link_encounter_to_appointment()

	def on_update(self):
		self._reconcile_appointment_encounter_links()

	def on_trash(self):
		self._clear_appointment_encounter_link()

	def _validate_branch_company_match(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} does not exist.").format(self.branch), title=_("Branch"))
		if branch_company != self.company:
			frappe.throw(_("Branch belongs to a different company."), title=_("Branch"))

	def _validate_patient(self):
		pdata = frappe.db.get_value(
			"Healthcare Patient",
			self.patient,
			["company", "branch", "active", "deceased"],
			as_dict=True,
		)
		if not pdata:
			frappe.throw(_("Patient does not exist."), title=_("Patient"))
		if pdata.company != self.company or pdata.branch != self.branch:
			frappe.throw(
				_("Patient must belong to the same company and branch as the encounter."),
				title=_("Patient"),
			)
		require_active = True
		try:
			raw = frappe.db.get_single_value(
				"Healthcare Settings", "require_active_patient_for_encounter"
			)
			if raw is not None:
				require_active = bool(cint(raw))
		except Exception:
			require_active = True
		if not pdata.active and require_active:
			frappe.throw(_("Inactive patient records cannot be used for new encounters."), title=_("Patient"))
		if pdata.deceased:
			frappe.throw(_("New encounters cannot be created for a deceased patient."), title=_("Patient"))

	def _validate_appointment_link(self):
		if not self.appointment:
			return
		appt = frappe.db.get_value(
			"Healthcare Appointment",
			self.appointment,
			["patient", "company", "branch", "department", "service_unit"],
			as_dict=True,
		)
		if not appt:
			frappe.throw(_("Appointment does not exist."), title=_("Appointment"))
		if appt.patient != self.patient:
			frappe.throw(_("Appointment patient must match encounter patient."), title=_("Appointment"))
		if appt.company != self.company or appt.branch != self.branch:
			frappe.throw(_("Appointment must belong to the same company and branch."), title=_("Appointment"))
		if self.department and appt.department and self.department != appt.department:
			frappe.throw(_("Department must match the linked appointment."), title=_("Department"))
		if self.service_unit and appt.service_unit and self.service_unit != appt.service_unit:
			frappe.throw(_("Service unit must match the linked appointment."), title=_("Service Unit"))

	def _validate_episode_of_care(self):
		if not self.episode_of_care:
			return
		ep = frappe.db.get_value(
			"Healthcare Episode Of Care",
			self.episode_of_care,
			["patient", "company", "branch", "status"],
			as_dict=True,
		)
		if not ep:
			frappe.throw(_("Episode of Care does not exist."), title=_("Episode"))
		if ep.patient != self.patient:
			frappe.throw(_("Episode patient must match encounter patient."), title=_("Episode"))
		if ep.company != self.company or ep.branch != self.branch:
			frappe.throw(_("Episode must belong to the same company and branch."), title=_("Episode"))
		if ep.status in ("finished", "cancelled"):
			frappe.throw(_("Cannot link encounters to a finished or cancelled episode."), title=_("Episode"))

	def _validate_single_encounter_per_appointment(self):
		if not self.appointment:
			return
		filters = {"appointment": self.appointment}
		if not self.is_new():
			filters["name"] = ["!=", self.name]
		other = frappe.db.exists("Healthcare Encounter", filters)
		if other:
			frappe.throw(
				_("Another encounter is already linked to this appointment ({0}).").format(other),
				title=_("Appointment"),
			)

	def _validate_location_hierarchy(self):
		if self.facility:
			f = frappe.db.get_value(
				"Healthcare Facility Profile",
				self.facility,
				["company", "branch"],
				as_dict=True,
			)
			if not f or f.company != self.company or f.branch != self.branch:
				frappe.throw(_("Facility must belong to the same company and branch."), title=_("Facility"))
		if self.department:
			d = frappe.db.get_value(
				"Healthcare Department",
				self.department,
				["company", "branch"],
				as_dict=True,
			)
			if not d or d.company != self.company or d.branch != self.branch:
				frappe.throw(_("Department must belong to the same company and branch."), title=_("Department"))
		if self.service_unit:
			u = frappe.db.get_value(
				"Healthcare Service Unit",
				self.service_unit,
				["company", "branch", "department"],
				as_dict=True,
			)
			if not u or u.company != self.company or u.branch != self.branch:
				frappe.throw(_("Service unit must belong to the same company and branch."), title=_("Service Unit"))
			if self.department and u.department and u.department != self.department:
				frappe.throw(_("Service unit must belong to the selected department."), title=_("Service Unit"))

	def _validate_period(self):
		if self.period_end and self.period_start and self.period_end < self.period_start:
			frappe.throw(_("Period end cannot be before period start."), title=_("Period"))

	def _link_encounter_to_appointment(self):
		if not self.appointment:
			return
		frappe.db.set_value(
			"Healthcare Appointment",
			self.appointment,
			"encounter",
			self.name,
			update_modified=False,
		)

	def _reconcile_appointment_encounter_links(self):
		prev = self.get_doc_before_save()
		if prev and prev.get("appointment"):
			if not self.appointment or prev.appointment != self.appointment:
				enc = frappe.db.get_value("Healthcare Appointment", prev.appointment, "encounter")
				if enc == self.name:
					frappe.db.set_value(
						"Healthcare Appointment",
						prev.appointment,
						"encounter",
						None,
						update_modified=False,
					)
		if self.appointment:
			frappe.db.set_value(
				"Healthcare Appointment",
				self.appointment,
				"encounter",
				self.name,
				update_modified=False,
			)

	def _clear_appointment_encounter_link(self):
		if not self.appointment:
			return
		current = frappe.db.get_value("Healthcare Appointment", self.appointment, "encounter")
		if current == self.name:
			frappe.db.set_value(
				"Healthcare Appointment",
				self.appointment,
				"encounter",
				None,
				update_modified=False,
			)

	def _sync_from_appointment(self):
		if not self.appointment:
			return
		appt = frappe.db.get_value(
			"Healthcare Appointment",
			self.appointment,
			["practitioner", "specialty", "branch", "company"],
			as_dict=True,
		)
		if not appt:
			return
		if appt.practitioner and not self.practitioner:
			self.practitioner = appt.practitioner
		if appt.specialty and not getattr(self, "specialty", None):
			if frappe.get_meta("Healthcare Encounter").has_field("specialty"):
				self.specialty = appt.specialty
		if appt.branch and not self.branch:
			self.branch = appt.branch
		if appt.company and not self.company:
			self.company = appt.company

	def _validate_diagnoses(self):
		for row in self.diagnoses or []:
			if not row.icd10_code:
				continue
			if not frappe.db.exists("Healthcare Icd10 Code", {"code": row.icd10_code, "is_active": 1}):
				continue
			desc = frappe.db.get_value("Healthcare Icd10 Code", {"code": row.icd10_code}, "description")
			if desc and (not row.description or (row.description or "").strip().lower() == "pending"):
				row.description = desc
