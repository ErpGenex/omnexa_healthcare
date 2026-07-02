# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document


class HealthcareTelemedicineConfiguration(Document):
    def validate(self):
        """Validate telemedicine configuration"""
        self.validate_session_durations()
    
    def validate_session_durations(self):
        """Validate session duration settings"""
        if self.default_session_duration and self.max_session_duration:
            if self.default_session_duration > self.max_session_duration:
                frappe.throw("Default session duration cannot exceed maximum session duration")
