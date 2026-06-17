# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Full patient registration gate — mandatory before booking (Global #1 patient experience)."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import getdate, validate_email_address

from omnexa_healthcare.api.patient_otp import send_patient_otp, verify_patient_otp

SESSION_PREFIX = "healthcare_patient_session:"
REQUIRED_ONLINE = ("given_name", "family_name", "gender", "birth_date", "phone", "national_id", "email", "company", "branch")
REQUIRED_RECEPTION = ("given_name", "family_name", "gender", "birth_date", "phone", "national_id", "company", "branch")


def _normalize_phone(phone: str) -> str:
	digits = re.sub(r"\D", "", phone or "")
	if len(digits) < 8:
		frappe.throw(_("Valid mobile number is required."), title=_("Registration"))
	return digits[-15:]


def _national_id_exists(national_id: str, branch: str | None = None) -> str | None:
	national_id = (national_id or "").strip()
	if not national_id:
		return None
	filters = {"identifier_type": "National ID", "value": national_id}
	for row in frappe.get_all(
		"Healthcare Patient Identifier",
		filters=filters,
		fields=["parent"],
		limit=5,
	):
		if not branch or frappe.db.get_value("Healthcare Patient", row.parent, "branch") == branch:
			return row.parent
	return None


def _phone_patient(phone: str, branch: str) -> str | None:
	phone = _normalize_phone(phone)
	row = frappe.db.sql(
		"""
		SELECT parent FROM `tabHealthcare Patient Telecom`
		WHERE value = %s AND parenttype = 'Healthcare Patient'
		LIMIT 1
		""",
		phone,
	)
	if not row:
		return None
	patient = row[0][0]
	if frappe.db.get_value("Healthcare Patient", patient, "branch") == branch:
		return patient
	return None


def registration_requirements(channel: str = "online") -> dict:
	req = list(REQUIRED_ONLINE if channel == "online" else REQUIRED_RECEPTION)
	return {
		"channel": channel,
		"required_fields": req,
		"otp_required": channel == "online",
		"booking_blocked_until": "Verified" if channel == "online" else "Complete",
	}


def is_registration_complete(patient: str, *, require_verified: bool = False) -> bool:
	if not frappe.db.exists("Healthcare Patient", patient):
		return False
	doc = frappe.get_doc("Healthcare Patient", patient)
	status = getattr(doc, "registration_status", None) or _infer_status(doc)
	if require_verified:
		return status == "Verified"
	return status in ("Complete", "Verified")


def _infer_status(doc) -> str:
	if not (doc.given_name and doc.family_name and doc.gender and doc.birth_date):
		return "Incomplete"
	has_phone = any((t.value or "").strip() for t in (doc.telecom or []) if (t.contact_system or "").lower() in ("phone", "mobile"))
	has_nid = any((i.identifier_type or "") == "National ID" and (i.value or "").strip() for i in (doc.identifiers or []))
	if has_phone and has_nid:
		return "Complete"
	return "Incomplete"


def assert_booking_allowed(patient: str, session_token: str | None = None, *, online: bool = False) -> None:
	if session_token:
		sess = frappe.cache().get_value(f"{SESSION_PREFIX}{session_token}")
		if not sess or sess.get("patient") != patient:
			frappe.throw(_("Invalid or expired session. Please verify OTP again."), title=_("Booking"))
		if online and not is_registration_complete(patient, require_verified=True):
			frappe.throw(_("Patient registration is incomplete."), title=_("Booking"))
		return
	if not is_registration_complete(patient, require_verified=online):
		frappe.throw(
			_("Complete patient registration before booking. Status: {0}").format(
				frappe.db.get_value("Healthcare Patient", patient, "registration_status") or "Incomplete"
			),
			title=_("Registration Required"),
		)


def _build_patient_doc(data: frappe._dict, status: str) -> frappe.Document:
	phone = _normalize_phone(data.phone)
	email = (data.email or "").strip().lower()
	if email:
		validate_email_address(email, throw=True)

	national_id = (data.national_id or "").strip()
	passport = (data.passport or "").strip()
	existing = _national_id_exists(national_id, data.branch) if national_id else None
	if existing:
		frappe.throw(_("National ID already registered for this branch."), title=_("Registration"))

	by_phone = _phone_patient(phone, data.branch)
	if by_phone:
		frappe.throw(_("Mobile number already registered. Please login with OTP."), title=_("Registration"))

	identifiers = []
	if national_id:
		identifiers.append(
			{
				"identifier_use": "official",
				"identifier_type": "National ID",
				"value": national_id,
				"is_primary_mrn": 0,
			}
		)
	if passport:
		identifiers.append(
			{
				"identifier_use": "official",
				"identifier_type": "Passport",
				"value": passport,
				"is_primary_mrn": 0,
			}
		)
	identifiers.append(
		{
			"identifier_use": "official",
			"identifier_type": "MRN",
			"value": f"REG-{phone[-8:]}",
			"is_primary_mrn": 1,
		}
	)

	telecom = [{"contact_system": "phone", "contact_use": "mobile", "value": phone, "rank": 1}]
	if email:
		telecom.append({"contact_system": "email", "contact_use": "home", "value": email, "rank": 2})

	payload = {
		"doctype": "Healthcare Patient",
		"naming_series": "HP-.#####",
		"company": data.company,
		"branch": data.branch,
		"given_name": data.given_name.strip(),
		"family_name": data.family_name.strip(),
		"gender": (data.gender or "").strip().lower(),
		"birth_date": getdate(data.birth_date),
		"nationality": data.get("nationality"),
		"city": data.get("city"),
		"address_line1": data.get("address_line1"),
		"active": 1,
		"registration_status": status,
		"identifiers": identifiers,
		"telecom": telecom,
	}
	if frappe.db.has_column("Healthcare Patient", "registration_status"):
		payload["registration_status"] = status
	return frappe.get_doc(payload)


def _ensure_portal_user(*, patient: str, given_name: str, family_name: str, phone: str, email: str, company: str) -> str:
	from omnexa_healthcare.api.web_booking import _ensure_portal_user as _web_user

	user = _web_user(given_name=given_name, family_name=family_name, phone=phone, email=email, company=company)
	if frappe.db.has_column("Healthcare Patient", "portal_user"):
		frappe.db.set_value("Healthcare Patient", patient, "portal_user", user)
	return user


@frappe.whitelist(allow_guest=True)
def get_registration_requirements(channel: str = "online") -> dict:
	return registration_requirements(channel)


@frappe.whitelist()
def register_patient_full(payload: str | dict) -> dict:
	"""Reception / desk — full registration in <30s, status Complete."""
	data = frappe._dict(frappe.parse_json(payload) if isinstance(payload, str) else payload or {})
	for key in REQUIRED_RECEPTION:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key.replace("_", " ").title()))
	doc = _build_patient_doc(data, "Complete")
	doc.flags.ignore_branch_access = True
	doc.insert(ignore_permissions=True)
	return {
		"patient": doc.name,
		"patient_name": doc.full_name or f"{doc.given_name} {doc.family_name}",
		"registration_status": "Complete",
		"message": _("Patient registered successfully."),
	}


@frappe.whitelist(allow_guest=True)
def register_patient_online(payload: str | dict) -> dict:
	"""Online portal — full registration then OTP."""
	data = frappe._dict(frappe.parse_json(payload) if isinstance(payload, str) else payload or {})
	for key in REQUIRED_ONLINE:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key.replace("_", " ").title()))
	doc = _build_patient_doc(data, "Complete")
	doc.flags.ignore_branch_access = True
	doc.insert(ignore_permissions=True)
	_ensure_portal_user(
		patient=doc.name,
		given_name=doc.given_name,
		family_name=doc.family_name,
		phone=data.phone,
		email=data.email,
		company=data.company,
	)
	otp_result = send_patient_otp(data.phone, doc.name)
	return {
		"patient": doc.name,
		"patient_name": doc.full_name or f"{doc.given_name} {doc.family_name}",
		"registration_status": "Complete",
		"otp_sent": True,
		"mobile": otp_result.get("mobile"),
		"demo_otp": otp_result.get("demo_otp"),
		"message": _("Registration complete. Enter OTP to verify before booking."),
	}


@frappe.whitelist(allow_guest=True)
def verify_registration_and_session(mobile: str, otp: str, patient: str) -> dict:
	"""Verify OTP and mark patient Verified for online booking."""
	result = verify_patient_otp(mobile, otp, patient)
	if frappe.db.has_column("Healthcare Patient", "registration_status"):
		frappe.db.set_value("Healthcare Patient", patient, "registration_status", "Verified")
	return {
		**result,
		"registration_status": "Verified",
		"booking_allowed": True,
	}


@frappe.whitelist(allow_guest=True)
def login_patient_otp(mobile: str) -> dict:
	"""Send OTP to existing registered patient mobile."""
	phone = _normalize_phone(mobile)
	patient = None
	for branch in frappe.get_all("Branch", pluck="name", limit=50):
		patient = _phone_patient(phone, branch)
		if patient:
			break
	if not patient:
		frappe.throw(_("No registered patient found for this mobile."), title=_("Login"))
	if not is_registration_complete(patient):
		frappe.throw(_("Please complete registration first."), title=_("Login"))
	return send_patient_otp(phone, patient)


@frappe.whitelist(allow_guest=True)
def check_booking_eligibility(patient: str | None = None, session_token: str | None = None) -> dict:
	if session_token:
		sess = frappe.cache().get_value(f"{SESSION_PREFIX}{session_token}")
		if sess and sess.get("patient"):
			patient = sess["patient"]
	if not patient:
		return {"allowed": False, "reason": "patient_required"}
	allowed = is_registration_complete(patient, require_verified=bool(session_token))
	status = frappe.db.get_value("Healthcare Patient", patient, "registration_status") if frappe.db.has_column(
		"Healthcare Patient", "registration_status"
	) else _infer_status(frappe.get_doc("Healthcare Patient", patient))
	return {"allowed": allowed, "patient": patient, "registration_status": status}
