# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from omnexa_healthcare.bed_units import is_companion_bed


class HealthcareCompanionStay(Document):
	def validate(self):
		self._validate_admission()
		self._validate_bed()
		self._validate_active_conflicts()
		if self.status == "discharged" and not self.check_out_datetime:
			self.check_out_datetime = now_datetime()

	def on_update(self):
		self._sync_bed_status()

	def after_insert(self):
		self._sync_bed_status()

	def _validate_admission(self):
		admit = frappe.db.get_value(
			"Healthcare Admission",
			self.admission,
			["patient", "status", "company", "branch"],
			as_dict=True,
		)
		if not admit:
			frappe.throw(_("Patient admission does not exist."), title=_("Admission"))
		if admit.patient != self.patient:
			frappe.throw(_("Companion stay patient must match admission patient."), title=_("Patient"))
		if admit.status != "admitted":
			frappe.throw(_("Patient must have an active admission before companion check-in."), title=_("Admission"))
		if admit.company != self.company or admit.branch != self.branch:
			frappe.throw(_("Admission must belong to the same company and branch."), title=_("Branch"))

	def _validate_bed(self):
		bed = frappe.db.get_value(
			"Healthcare Bed",
			self.bed,
			["bed_type", "status", "company", "branch"],
			as_dict=True,
		)
		if not bed:
			frappe.throw(_("Companion bed does not exist."), title=_("Bed"))
		if not is_companion_bed(bed.bed_type):
			frappe.throw(_("Selected bed is not a companion lodging bed."), title=_("Bed"))
		if bed.company != self.company or bed.branch != self.branch:
			frappe.throw(_("Bed must belong to the same company and branch."), title=_("Branch"))

	def _validate_active_conflicts(self):
		if self.status != "active":
			return
		bed_filter = {"bed": self.bed, "status": "active"}
		if self.name:
			bed_filter["name"] = ["!=", self.name]
		if frappe.db.exists("Healthcare Companion Stay", bed_filter):
			frappe.throw(_("This companion bed is already occupied."), title=_("Bed"))

	def _sync_bed_status(self):
		if not self.bed:
			return
		if self.status == "active":
			frappe.db.set_value("Healthcare Bed", self.bed, "status", "Occupied", update_modified=False)
		elif self.status in ("discharged", "cancelled"):
			frappe.db.set_value("Healthcare Bed", self.bed, "status", "Available", update_modified=False)
