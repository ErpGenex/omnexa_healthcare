# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.model.document import Document

from omnexa_healthcare.api.specialty_emr import validate_icd10_code, validate_icd11_code


class HealthcareEncounterDiagnosis(Document):
	def validate(self):
		if self.icd11_code:
			if frappe.db.exists("Healthcare Icd11 Code", {"code": self.icd11_code, "is_active": 1}):
				row = frappe.db.get_value(
					"Healthcare Icd11 Code",
					{"code": self.icd11_code},
					["description", "icd10_map"],
					as_dict=True,
				)
				if row:
					if row.description and (not self.description or (self.description or "").strip().lower() == "pending"):
						self.description = row.description
					if row.icd10_map and not self.icd10_code:
						self.icd10_code = row.icd10_map
			else:
				validate_icd11_code(self.icd11_code)
		if not self.icd10_code:
			return
		if frappe.db.exists("Healthcare Icd10 Code", {"code": self.icd10_code, "is_active": 1}):
			desc = frappe.db.get_value("Healthcare Icd10 Code", {"code": self.icd10_code}, "description")
			if desc and (not self.description or (self.description or "").strip().lower() == "pending"):
				self.description = desc
			return
		validate_icd10_code(self.icd10_code)
