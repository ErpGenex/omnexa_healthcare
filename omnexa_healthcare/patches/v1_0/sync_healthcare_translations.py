# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_healthcare.i18n.sync_healthcare_translations import sync_healthcare_translations


def execute():
	stats = sync_healthcare_translations(write=True)
	frappe.logger("omnexa_healthcare").info(f"sync_healthcare_translations: {stats}")
