# -*- coding: utf-8 -*-
import frappe

from omnexa_healthcare.api.telemedicine_admin import ensure_telemedicine_configuration


def execute():
	ensure_telemedicine_configuration()
	frappe.db.commit()
