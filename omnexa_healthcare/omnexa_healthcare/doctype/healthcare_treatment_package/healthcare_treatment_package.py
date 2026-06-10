# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class HealthcareTreatmentPackage(Document):
	def validate(self):
		total = 0
		for row in self.items or []:
			row.amount = flt(row.qty) * flt(row.rate)
			total += row.amount
		if total and not self.total_price:
			self.total_price = total


@frappe.whitelist()
def apply_package_to_service_charge(package: str, patient: str, company: str, branch: str | None = None) -> dict:
	pkg = frappe.get_doc("Healthcare Treatment Package", package)
	charge = frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": patient,
			"company": company,
			"branch": branch,
			"status": "Draft",
		}
	)
	for row in pkg.items or []:
		charge.append(
			"items",
			{
				"item_code": row.item_code,
				"description": row.procedure or row.item_code,
				"qty": row.qty,
				"rate": row.rate,
			},
		)
	charge.insert(ignore_permissions=True)
	return {"service_charge": charge.name, "package": package}
