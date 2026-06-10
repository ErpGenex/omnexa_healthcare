# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, getdate


class HealthcareInstallmentPlan(Document):
	def validate(self):
		if not self.installments and self.installment_count and self.total_amount:
			self._generate_installments()

	def _generate_installments(self):
		self.installments = []
		per = float(self.total_amount) / int(self.installment_count)
		due = getdate()
		for i in range(1, int(self.installment_count) + 1):
			if i > 1:
				due = add_months(due, 1 if self.frequency == "Monthly" else (3 if self.frequency == "Quarterly" else 0))
			self.append("installments", {"installment_no": i, "due_date": due, "amount": per})


@frappe.whitelist()
def create_installment_plan(patient: str, total_amount: float, installment_count: int, company: str, **kwargs) -> dict:
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Installment Plan",
			"patient": patient,
			"total_amount": total_amount,
			"installment_count": installment_count,
			"company": company,
			"frequency": kwargs.get("frequency") or "Monthly",
			"service_charge": kwargs.get("service_charge"),
			"sales_invoice": kwargs.get("sales_invoice"),
			"branch": kwargs.get("branch"),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "installments": len(doc.installments)}
