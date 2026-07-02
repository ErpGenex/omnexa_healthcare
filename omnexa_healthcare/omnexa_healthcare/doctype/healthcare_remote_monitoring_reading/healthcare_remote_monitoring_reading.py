# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class HealthcareRemoteMonitoringReading(Document):
    def validate(self):
        """Validate remote monitoring reading"""
        self.validate_reading_datetime()
    
    def validate_reading_datetime(self):
        """Validate reading datetime"""
        if self.reading_datetime and get_datetime(self.reading_datetime) > get_datetime(now_datetime()):
            frappe.throw("Reading datetime cannot be in the future")
