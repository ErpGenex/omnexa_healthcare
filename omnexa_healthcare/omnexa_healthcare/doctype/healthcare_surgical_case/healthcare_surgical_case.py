# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareSurgicalCase(Document):
	def validate(self):
		self._validate_or_availability()

	def on_update(self):
		if self.status == "In Progress":
			frappe.db.set_value("Healthcare Operating Room", self.operating_room, "status", "In Use", update_modified=False)
			self._ensure_anesthesia_record()
		elif self.status in ("Completed", "Cancelled"):
			frappe.db.set_value("Healthcare Operating Room", self.operating_room, "status", "Available", update_modified=False)
			if self.status == "Completed":
				self._on_case_completed()

	def _validate_or_availability(self):
		if not self.operating_room or self.status in ("Completed", "Cancelled"):
			return
		conflict = frappe.db.sql(
			"""
			SELECT name FROM `tabHealthcare Surgical Case`
			WHERE operating_room = %s AND name != %s AND status IN ('Scheduled', 'In Progress')
			  AND scheduled_start < %s AND IFNULL(scheduled_end, scheduled_start) > %s
			LIMIT 1
			""",
			(self.operating_room, self.name or "", self.scheduled_end or self.scheduled_start, self.scheduled_start),
		)
		if conflict:
			frappe.throw(_("Operating room is already booked for this time slot."), title=_("OR Conflict"))

	def _ensure_anesthesia_record(self):
		if self.anesthesia_record:
			return
		anesthesiologist = None
		for row in self.surgical_team or []:
			if row.role == "Anesthesiologist" and row.practitioner:
				anesthesiologist = row.practitioner
				break
		record = frappe.get_doc(
			{
				"doctype": "Healthcare Anesthesia Record",
				"surgical_case": self.name,
				"anesthesiologist": anesthesiologist,
				"start_time": self.scheduled_start,
				"company": self.company,
				"branch": self.branch,
			}
		).insert(ignore_permissions=True)
		self.db_set("anesthesia_record", record.name, update_modified=False)

	def _on_case_completed(self):
		if not self.service_charge:
			from omnexa_healthcare.api.billing_automation import create_service_charge_from_surgical_case

			create_service_charge_from_surgical_case(self.name)
		if self.anesthesia_record:
			frappe.db.set_value(
				"Healthcare Anesthesia Record",
				self.anesthesia_record,
				"end_time",
				self.scheduled_end or self.scheduled_start,
				update_modified=False,
			)
