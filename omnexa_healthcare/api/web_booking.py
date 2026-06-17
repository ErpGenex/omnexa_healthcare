# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Public website APIs for healthcare service catalog and online booking."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, validate_email_address, validate_phone_number

from frappe.utils import get_url

from omnexa_healthcare.api.patient_registration import (
	assert_booking_allowed,
	register_patient_online,
	verify_registration_and_session,
)
from omnexa_healthcare.api.scheduling import create_healthcare_appointment
from omnexa_healthcare.scheduling_engine import get_available_slots


def _public_image(path: str | None) -> str:
	if not path:
		return ""
	if path.startswith(("http://", "https://")):
		return path
	return get_url(path)


@frappe.whitelist(allow_guest=True)
def get_published_services(company: str, branch: str) -> list[dict]:
	"""List services published on the website for a branch."""
	if not (company and branch):
		frappe.throw(_("Company and branch are required"))
	if frappe.db.get_value("Branch", branch, "company") != company:
		frappe.throw(_("Branch does not belong to company"))

	rows = frappe.get_all(
		"Healthcare Service Catalog",
		filters={
			"company": company,
			"branch": branch,
			"is_active": 1,
			"publish_on_website": 1,
		},
		fields=[
			"name",
			"service_code",
			"service_title",
			"specialty",
			"service_type",
			"default_rate",
			"duration_mins",
			"department",
			"default_practitioner",
			"website_description",
			"website_image",
			"display_order",
		],
		order_by="display_order asc, service_title asc",
	)
	for row in rows:
		row["website_image"] = _public_image(row.get("website_image"))
	return rows


@frappe.whitelist(allow_guest=True)
def get_booking_slots(
	company: str,
	branch: str,
	service_code: str,
	date: str,
) -> dict:
	"""Return practitioner and open slots for a published service on a date."""
	if not (company and branch and service_code and date):
		frappe.throw(_("Company, branch, service code and date are required"))

	catalog = frappe.db.get_value(
		"Healthcare Service Catalog",
		{
			"service_code": service_code,
			"company": company,
			"branch": branch,
			"is_active": 1,
			"publish_on_website": 1,
		},
		[
			"name",
			"service_title",
			"specialty",
			"default_practitioner",
			"default_rate",
			"duration_mins",
			"department",
		],
		as_dict=True,
	)
	if not catalog:
		frappe.throw(_("Service is not available for online booking."))

	practitioner = catalog.default_practitioner
	if not practitioner:
		frappe.throw(_("No practitioner configured for this service."))

	slots = get_available_slots(practitioner, branch, date, specialty=catalog.specialty)
	return {
		"service": catalog,
		"practitioner": practitioner,
		"practitioner_name": frappe.db.get_value("Healthcare Practitioner", practitioner, "practitioner_name"),
		"slots": slots,
	}


@frappe.whitelist(allow_guest=True)
def book_appointment_online(payload: str | dict) -> dict:
	"""Create a website booking — requires verified patient session (full registration + OTP)."""
	data = frappe.parse_json(payload) if isinstance(payload, str) else frappe._dict(payload or {})
	required = (
		"company",
		"branch",
		"service_code",
		"appointment_date",
		"slot_end",
		"patient",
		"session_token",
	)
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key.replace("_", " ").title()))

	assert_booking_allowed(data.patient, session_token=data.session_token, online=True)
	patient = data.patient

	catalog = frappe.db.get_value(
		"Healthcare Service Catalog",
		{
			"service_code": data.service_code,
			"company": data.company,
			"branch": data.branch,
			"is_active": 1,
			"publish_on_website": 1,
		},
		[
			"specialty",
			"default_practitioner",
			"default_rate",
			"department",
			"service_type",
			"duration_mins",
		],
		as_dict=True,
	)
	if not catalog:
		frappe.throw(_("Service is not available for online booking."))

	practitioner = data.get("practitioner") or catalog.default_practitioner
	if not practitioner:
		frappe.throw(_("No practitioner available for booking."))

	slot_start = get_datetime(data.appointment_date)
	slot_end = get_datetime(data.slot_end)
	if not slot_end and catalog.duration_mins:
		slot_end = slot_start + timedelta(minutes=cint(catalog.duration_mins))

	result = create_healthcare_appointment(
		frappe._dict(
			{
				"patient": patient,
				"practitioner": practitioner,
				"branch": data.branch,
				"company": data.company,
				"specialty": catalog.specialty,
				"department": catalog.department,
				"appointment_date": str(slot_start),
				"slot_end": str(slot_end),
				"appointment_type": catalog.service_type
				if catalog.service_type in ("Consultation", "Follow-up", "Telehealth")
				else "Consultation",
				"booking_fee": flt(data.booking_fee) or flt(catalog.default_rate),
				"payment_status": data.get("payment_status") or "Unpaid",
				"booking_channel": "Website",
			}
		),
		ignore_permissions=True,
	)
	return {
		**result,
		"patient": patient,
		"user": frappe.db.get_value("Healthcare Patient", patient, "portal_user"),
		"message": _("Appointment booked successfully."),
	}


@frappe.whitelist(allow_guest=True)
def register_for_booking(payload: str | dict) -> dict:
	"""Step 1: Full patient registration + OTP (online booking gate)."""
	return register_patient_online(payload)


@frappe.whitelist(allow_guest=True)
def verify_for_booking(mobile: str, otp: str, patient: str) -> dict:
	"""Step 2: OTP verification — returns session_token for booking."""
	return verify_registration_and_session(mobile, otp, patient)


def _resolve_or_create_patient(
	*,
	company: str,
	branch: str,
	given_name: str,
	family_name: str,
	phone: str,
	email: str | None = None,
) -> str:
	phone = (phone or "").strip()
	existing = frappe.db.sql(
		"""
		SELECT parent
		FROM `tabHealthcare Patient Telecom`
		WHERE value = %s AND parenttype = 'Healthcare Patient'
		LIMIT 1
		""",
		phone,
	)
	if existing:
		patient = existing[0][0]
		if frappe.db.get_value("Healthcare Patient", patient, "branch") == branch:
			return patient

	telecom = [{"contact_system": "phone", "contact_use": "mobile", "value": phone, "rank": 1}]
	if email:
		telecom.append({"contact_system": "email", "contact_use": "home", "value": email, "rank": 2})

	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Patient",
			"naming_series": "HP-.#####",
			"company": company,
			"branch": branch,
			"given_name": given_name,
			"family_name": family_name,
			"active": 1,
			"identifiers": [
				{
					"identifier_use": "official",
					"identifier_type": "MRN",
					"value": f"WEB-{phone[-8:]}",
					"is_primary_mrn": 1,
				}
			],
			"telecom": telecom,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _portal_role() -> str:
	return "Patient Portal User" if frappe.db.exists("Role", "Patient Portal User") else "Customer"


def _portal_email(email: str | None, phone: str, company: str) -> str:
	clean_email = (email or "").strip().lower()
	if clean_email and validate_email_address(clean_email):
		return clean_email
	abbr = (frappe.db.get_value("Company", company, "abbr") or "HC").lower()
	digits = "".join(ch for ch in (phone or "") if ch.isdigit())[-10:] or "0000000000"
	return f"{abbr}.{digits}@patient.omnexa.portal"


def _ensure_portal_user(
	*,
	given_name: str,
	family_name: str,
	phone: str,
	email: str | None,
	company: str,
) -> str | None:
	resolved_email = _portal_email(email, phone, company)
	existing = frappe.db.get_value("User", resolved_email, "name")
	if not existing and email:
		existing = frappe.db.get_value("User", {"email": (email or "").strip().lower()}, "name")
	if not existing and phone:
		existing = frappe.db.get_value("User", {"mobile_no": phone}, "name")
	if existing:
		_ensure_portal_role(existing)
		return existing

	user_data = {
		"doctype": "User",
		"email": resolved_email,
		"first_name": given_name,
		"last_name": family_name,
		"send_welcome_email": 0,
		"user_type": "Website User",
	}
	try:
		validate_phone_number(phone, throw=True)
		user_data["mobile_no"] = phone
	except Exception:
		pass

	user = frappe.get_doc(user_data).insert(ignore_permissions=True)
	user.add_roles(_portal_role())
	return user.name


def _ensure_portal_role(user: str) -> None:
	role = _portal_role()
	if role and not frappe.db.exists("Has Role", {"parent": user, "role": role}):
		doc = frappe.get_doc("User", user)
		doc.add_roles(role)
