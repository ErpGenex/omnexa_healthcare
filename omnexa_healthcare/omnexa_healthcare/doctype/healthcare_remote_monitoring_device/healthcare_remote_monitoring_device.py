# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document


class HealthcareRemoteMonitoringDevice(Document):
    def validate(self):
        """Validate remote monitoring device"""
        self.validate_serial_number()
    
    def validate_serial_number(self):
        """Validate serial number uniqueness"""
        if self.serial_number:
            existing = frappe.db.exists("Healthcare Remote Monitoring Device", {
                "serial_number": self.serial_number,
                "name": ["!=", self.name]
            })
            if existing:
                frappe.throw("A device with this serial number already exists")
