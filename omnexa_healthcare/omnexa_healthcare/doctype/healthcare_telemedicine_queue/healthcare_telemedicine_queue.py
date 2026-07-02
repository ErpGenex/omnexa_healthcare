# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document


class HealthcareTelemedicineQueue(Document):
    def validate(self):
        """Validate telemedicine queue"""
        self.validate_queue_position()
    
    def validate_queue_position(self):
        """Validate queue position"""
        if self.queue_position and self.queue_position < 1:
            frappe.throw("Queue position must be at least 1")
