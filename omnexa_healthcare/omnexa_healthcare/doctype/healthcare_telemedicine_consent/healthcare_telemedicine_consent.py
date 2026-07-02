# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document


class HealthcareTelemedicineConsent(Document):
    def validate(self):
        """Validate telemedicine consent"""
        self.validate_consent_date()
    
    def validate_consent_date(self):
        """Validate consent date"""
        # Allow consent date to be in the future (for scheduled sessions)
        # Only validate if it's too far in the future (more than 1 year)
        if self.consent_date:
            from frappe.utils import add_days
            max_future_date = add_days(frappe.utils.nowdate(), 365)
            if self.consent_date > max_future_date:
                frappe.throw("Consent date cannot be more than 1 year in the future")
