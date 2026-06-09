# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Auto billing from appointments, encounters, and procedure orders."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


@frappe.whitelist()
def create_service_charge_from_appointment(appointment: str) -> dict:
	appt = frappe.get_doc("Healthcare Appointment", appointment)
	if appt.service_charge:
		return {"name": appt.service_charge, "created": False}

	if not appt.patient:
		frappe.throw(_("Patient is required"))

	patient = frappe.db.get_value(
		"Healthcare Patient",
		appt.patient,
		["billing_customer", "company", "branch"],
		as_dict=True,
	)
	if not patient or not patient.billing_customer:
		frappe.throw(_("Set billing customer on patient before invoicing."), title=_("Billing"))

	item, rate = _resolve_appointment_fee(appt)
	if not item and not flt(appt.booking_fee):
		frappe.throw(_("No fee rule or booking fee on appointment."), title=_("Billing"))

	charge = frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": appt.patient,
			"billing_customer": patient.billing_customer,
			"company": appt.company,
			"branch": appt.branch,
			"posting_date": getdate(appt.appointment_date or today()),
			"status": "Draft",
			"items": [
				{
					"item": item,
					"qty": 1,
					"rate": flt(rate) or flt(appt.booking_fee),
					"amount": flt(rate) or flt(appt.booking_fee),
				}
			]
			if item
			else [],
		}
	)
	if not charge.items and flt(appt.booking_fee):
		frappe.throw(_("Configure default Item on consultation fee rule or service catalog."), title=_("Billing"))
	charge.insert()
	appt.db_set("service_charge", charge.name, update_modified=False)
	return {"name": charge.name, "created": True}


def _resolve_appointment_fee(appt) -> tuple[str | None, float]:
	if flt(appt.booking_fee):
		catalog = frappe.db.get_value(
			"Healthcare Service Catalog",
			{"specialty": appt.specialty, "service_type": appt.appointment_type or "Consultation", "is_active": 1},
			["default_item", "default_rate"],
			as_dict=True,
		)
		if catalog and catalog.default_item:
			return catalog.default_item, flt(appt.booking_fee) or flt(catalog.default_rate)

	filters = {"specialty": appt.specialty, "company": appt.company}
	if appt.appointment_type:
		filters["appointment_type"] = appt.appointment_type
	rule = frappe.db.get_value(
		"Healthcare Consultation Fee Rule",
		filters,
		["default_item", "first_visit_rate", "follow_up_rate"],
		as_dict=True,
	)
	if rule:
		rate = flt(rule.follow_up_rate if appt.appointment_type == "Follow-up" else rule.first_visit_rate)
		return rule.default_item, rate
	return None, flt(appt.booking_fee)


@frappe.whitelist()
def create_service_charge_from_procedure_order(procedure_order: str) -> dict:
	order = frappe.get_doc("Healthcare Procedure Order", procedure_order)
	if order.service_charge:
		return {"name": order.service_charge, "created": False}
	proc = frappe.get_doc("Healthcare Procedure", order.procedure)
	patient = frappe.db.get_value(
		"Healthcare Patient",
		order.patient,
		["billing_customer"],
		as_dict=True,
	)
	if not patient or not patient.billing_customer:
		frappe.throw(_("Set billing customer on patient."), title=_("Billing"))
	if not proc.default_item:
		frappe.throw(_("Procedure {0} has no default item.").format(proc.name), title=_("Billing"))

	rate = flt(proc.default_rate)
	charge = frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": order.patient,
			"billing_customer": patient.billing_customer,
			"company": order.company,
			"branch": order.branch,
			"posting_date": getdate(order.planned_date or today()),
			"status": "Draft",
			"items": [{"item": proc.default_item, "qty": 1, "rate": rate, "amount": rate}],
		}
	)
	charge.insert()
	order.db_set("service_charge", charge.name, update_modified=False)
	return {"name": charge.name, "created": True}


@frappe.whitelist()
def create_service_charge_from_surgical_case(surgical_case: str) -> dict:
	case = frappe.get_doc("Healthcare Surgical Case", surgical_case)
	if case.service_charge:
		return {"name": case.service_charge, "created": False}
	proc = frappe.get_doc("Healthcare Procedure", case.procedure)
	patient = frappe.db.get_value(
		"Healthcare Patient",
		case.patient,
		["billing_customer"],
		as_dict=True,
	)
	if not patient or not patient.billing_customer:
		frappe.throw(_("Set billing customer on patient."), title=_("Billing"))
	if not proc.default_item:
		frappe.throw(_("Procedure {0} has no default item.").format(proc.name), title=_("Billing"))

	rate = flt(proc.default_rate)
	charge = frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": case.patient,
			"billing_customer": patient.billing_customer,
			"company": case.company,
			"branch": case.branch,
			"posting_date": getdate(case.scheduled_start or today()),
			"status": "Draft",
			"items": [{"item": proc.default_item, "qty": 1, "rate": rate, "amount": rate}],
		}
	)
	charge.insert()
	case.db_set("service_charge", charge.name, update_modified=False)
	return {"name": charge.name, "created": True}
