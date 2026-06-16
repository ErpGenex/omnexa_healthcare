# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class HealthcareFamilyUnit(Document):
	def validate(self):
		self._ensure_head_in_members()
		self._validate_unique_family_number()

	def _ensure_head_in_members(self):
		if not self.head_of_family:
			return
		head_rows = [m for m in (self.members or []) if m.patient == self.head_of_family]
		if not head_rows:
			self.append(
				"members",
				{
					"patient": self.head_of_family,
					"relationship": "Head",
					"is_primary_contact": 1,
				},
			)
			return
		for row in head_rows:
			row.relationship = "Head"
			if not any(m.is_primary_contact for m in self.members or []):
				row.is_primary_contact = 1

	def _validate_unique_family_number(self):
		if not self.family_number:
			return
		existing = frappe.db.get_value(
			"Healthcare Family Unit",
			{"family_number": self.family_number, "name": ["!=", self.name or ""]},
			"name",
		)
		if existing:
			frappe.throw(
				_("Family number {0} is already used by {1}.").format(self.family_number, existing),
				title=_("Family Unit"),
			)
