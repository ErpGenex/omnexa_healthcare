# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.model.document import Document

from omnexa_healthcare.observation_profiles import default_ucum_for_profile


class HealthcareObservation(Document):
	def validate(self):
		if not self.unit_ucum and self.observation_profile:
			self.unit_ucum = default_ucum_for_profile(self.observation_profile)
