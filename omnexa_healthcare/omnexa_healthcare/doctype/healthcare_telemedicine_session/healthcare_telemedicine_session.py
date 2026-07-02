# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime


class HealthcareTelemedicineSession(Document):
    def validate(self):
        """Validate telemedicine session"""
        self.validate_dates()
        self.validate_practitioner_availability()
    
    def validate_dates(self):
        """Validate session dates"""
        if self.scheduled_datetime and self.end_datetime:
            if get_datetime(self.scheduled_datetime) > get_datetime(self.end_datetime):
                frappe.throw("End datetime cannot be before scheduled datetime")
    
    def validate_practitioner_availability(self):
        """Validate practitioner availability"""
        if self.practitioner and self.scheduled_datetime and self.status in ("Scheduled", "In Progress"):
            end_time = self.end_datetime or self.scheduled_datetime
            overlapping = frappe.db.exists(
                "Healthcare Telemedicine Session",
                {
                    "practitioner": self.practitioner,
                    "scheduled_datetime": ["<=", get_datetime(end_time)],
                    "end_datetime": [">=", get_datetime(self.scheduled_datetime)],
                    "status": ["in", ["Scheduled", "In Progress"]],
                    "name": ["!=", self.name],
                },
            )
            
            if overlapping:
                frappe.throw("Practitioner has an overlapping session at this time")
