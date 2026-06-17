# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Omnexa Journey Desk — unified APIs for Reception · Cashier · Physician · Patient."""

from __future__ import annotations

import hashlib
import hmac
import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, today

from omnexa_healthcare.api.patient_registration import assert_booking_allowed, register_patient_full
from omnexa_healthcare.api.scheduling import create_healthcare_appointment
from omnexa_healthcare.scheduling_engine import get_available_slots


def _journey_token(appointment: str, patient: str) -> str:
	secret = frappe.get_site_config().get("secret_key") or "omnexa-journey"
	raw = json.dumps({"appt": appointment, "patient": patient, "ts": str(now_datetime())}, sort_keys=True)
	sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:24]
	return f"JRN-{appointment}-{sig}"


@frappe.whitelist()
def get_reception_kpis(company: str | None = None, branch: str | None = None) -> dict:
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	filters = {"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]]}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	rev_sql = """
		SELECT IFNULL(SUM(booking_fee), 0) FROM `tabHealthcare Appointment`
		WHERE appointment_date BETWEEN %s AND %s AND payment_status = 'Paid'
	"""
	rev_params: list = [f"{today()} 00:00:00", f"{today()} 23:59:59"]
	if branch:
		rev_sql += " AND branch = %s"
		rev_params.append(branch)
	return {
		"appointments_today": frappe.db.count("Healthcare Appointment", filters),
		"new_patients_today": frappe.db.count(
			"Healthcare Patient",
			{"creation": [">=", f"{today()} 00:00:00"], **({"branch": branch} if branch else {})},
		),
		"revenue_today": flt(frappe.db.sql(rev_sql, rev_params)[0][0]),
		"avg_wait_mins": 15,
	}


@frappe.whitelist()
def get_reception_clinics(company: str, branch: str) -> list[dict]:
	"""Intelligent clinic cards — specialty, doctors, waiting queue."""
	clinics: list[dict] = []
	seen: set[str] = set()

	# Primary source: specialties from active practitioner branch assignments
	for row in frappe.db.sql(
		"""
		SELECT pb.specialty, COUNT(DISTINCT p.name) AS doctor_count
		FROM `tabHealthcare Practitioner` p
		INNER JOIN `tabHealthcare Practitioner Branch` pb ON pb.parent = p.name
		WHERE p.company = %s AND p.status = 'Active'
			AND pb.branch = %s AND IFNULL(pb.is_active, 0) = 1
			AND pb.specialty IS NOT NULL AND pb.specialty != ''
		GROUP BY pb.specialty
		ORDER BY pb.specialty ASC
		LIMIT 20
		""",
		(company, branch),
		as_dict=True,
	):
		spec = row.specialty
		if spec in seen:
			continue
		seen.add(spec)
		waiting = frappe.db.count(
			"Healthcare Appointment",
			{
				"branch": branch,
				"specialty": spec,
				"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]],
				"status": ["in", ["Scheduled", "Arrived"]],
			},
		)
		spec_title = frappe.db.get_value("Healthcare Specialty", spec, "specialty_name") or spec
		clinics.append(
			{
				"id": spec,
				"specialty": spec,
				"name": spec_title,
				"subtitle": _("Outpatient clinic"),
				"doctor_count": cint(row.doctor_count),
				"waiting_count": waiting,
				"icon": "🏥",
			}
		)

	if clinics:
		return clinics

	# Fallback: published service catalog
	for svc in frappe.get_all(
		"Healthcare Service Catalog",
		filters={"company": company, "branch": branch, "is_active": 1, "publish_on_website": 1},
		fields=["specialty", "department"],
		limit=20,
	):
		spec = svc.get("specialty") or svc.get("department")
		if not spec or spec in seen:
			continue
		seen.add(spec)
		clinics.append(
			{
				"id": spec,
				"specialty": spec,
				"name": spec,
				"subtitle": _("Outpatient clinic"),
				"doctor_count": 0,
				"waiting_count": 0,
				"icon": "🏥",
			}
		)

	if clinics:
		return clinics

	# Last fallback: active departments
	for d in frappe.get_all(
		"Healthcare Department",
		filters={"company": company, "branch": branch, "status": "Active"},
		fields=["name", "department_name", "department_code"],
		limit=20,
	):
		spec = d.department_name
		if spec in seen:
			continue
		seen.add(spec)
		clinics.append(
			{
				"id": d.name,
				"specialty": d.name,
				"name": d.department_name,
				"subtitle": _("Department"),
				"doctor_count": 0,
				"waiting_count": 0,
				"icon": "🏥",
			}
		)
	return clinics


@frappe.whitelist()
def get_reception_doctors(company: str, branch: str, specialty: str | None = None) -> list[dict]:
	practitioner_names = frappe.db.sql(
		"""
		SELECT DISTINCT p.name
		FROM `tabHealthcare Practitioner` p
		INNER JOIN `tabHealthcare Practitioner Branch` pb ON pb.parent = p.name
		WHERE p.company = %s AND p.status = 'Active'
			AND pb.branch = %s AND IFNULL(pb.is_active, 0) = 1
			{specialty_filter}
		ORDER BY p.practitioner_name ASC
		LIMIT 30
		""".format(
			specialty_filter="AND pb.specialty = %s" if specialty else ""
		),
		(company, branch, specialty) if specialty else (company, branch),
	)
	names = [r[0] for r in practitioner_names]
	if not names:
		return []

	out = []
	for r in frappe.get_all(
		"Healthcare Practitioner",
		filters={"name": ["in", names]},
		fields=["name", "practitioner_name", "license_number", "website_rating"],
	):
		doc = frappe.get_doc("Healthcare Practitioner", r.name)
		ba = next(
			(
				b
				for b in (doc.branch_assignments or [])
				if b.branch == branch and b.is_active and (not specialty or b.specialty == specialty)
			),
			None,
		)
		spec = ba.specialty if ba else specialty
		queue_count = frappe.db.count(
			"Healthcare Appointment",
			{
				"practitioner": r.name,
				"branch": branch,
				"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]],
				"status": ["in", ["Scheduled", "Arrived", "In Consultation"]],
			},
		)
		slots = get_available_slots(r.name, branch, today(), specialty=spec) if spec else []
		next_slot = slots[0]["start"] if slots else _("Today")
		out.append(
			{
				**r,
				"specialty": spec,
				"specialty_name": frappe.db.get_value("Healthcare Specialty", spec, "specialty_name") if spec else "",
				"queue_count": queue_count,
				"next_slot": next_slot,
				"rating": str(r.website_rating or "4.9"),
				"consultation_fee": flt(ba.consultation_fee) if ba else 0,
			}
		)
	return out


@frappe.whitelist()
def search_patient_quick(query: str, branch: str | None = None) -> list[dict]:
	"""Search by National ID, MRN, mobile, passport, name."""
	q = (query or "").strip()
	if len(q) < 2:
		return []
	results: list[dict] = []
	# Identifier lookup
	for id_row in frappe.get_all(
		"Healthcare Patient Identifier",
		filters={"value": ["like", f"%{q}%"]},
		fields=["parent", "identifier_type", "value"],
		limit=10,
	):
		p = frappe.db.get_value(
			"Healthcare Patient",
			id_row.parent,
			["name", "patient_name", "gender", "birth_date", "branch"],
			as_dict=True,
		)
		if p and (not branch or p.branch == branch):
			results.append({**p, "match_type": id_row.identifier_type, "match_value": id_row.value})
	# Telecom
	for tel in frappe.get_all(
		"Healthcare Patient Telecom",
		filters={"value": ["like", f"%{q}%"]},
		fields=["parent", "value"],
		limit=10,
	):
		if any(r["name"] == tel.parent for r in results):
			continue
		p = frappe.db.get_value("Healthcare Patient", tel.parent, ["name", "patient_name", "gender", "birth_date", "branch"], as_dict=True)
		if p and (not branch or p.branch == branch):
			results.append({**p, "match_type": "Mobile", "match_value": tel.value})
	# Name
	if len(q) >= 3:
		for p in frappe.get_all(
			"Healthcare Patient",
			filters={"patient_name": ["like", f"%{q}%"], **({"branch": branch} if branch else {})},
			fields=["name", "patient_name", "gender", "birth_date", "branch"],
			limit=10,
		):
			if not any(r["name"] == p.name for r in results):
				results.append({**p, "match_type": "Name", "match_value": p.patient_name})
	return results[:15]


@frappe.whitelist()
def quick_register_patient(payload: str | dict) -> dict:
	"""Reception desk — full patient registration in one call."""
	return register_patient_full(payload)


@frappe.whitelist()
def create_reception_booking(
	patient: str,
	practitioner: str,
	company: str,
	branch: str,
	specialty: str,
	appointment_date: str,
	slot_end: str | None = None,
	appointment_type: str = "Consultation",
	booking_fee: float = 0,
	session_token: str | None = None,
) -> dict:
	assert_booking_allowed(patient, session_token=session_token, online=False)
	result = create_healthcare_appointment(
		frappe._dict(
			{
				"patient": patient,
				"practitioner": practitioner,
				"branch": branch,
				"company": company,
				"specialty": specialty,
				"appointment_date": appointment_date,
				"slot_end": slot_end or appointment_date,
				"appointment_type": appointment_type,
				"booking_fee": flt(booking_fee),
				"payment_status": "Unpaid",
				"booking_channel": "Reception Desk",
			}
		)
	)
	token = issue_visit_token(result.get("name") or result.get("appointment"))
	return {**result, **token}


@frappe.whitelist()
def issue_visit_token(appointment: str) -> dict:
	doc = frappe.get_doc("Healthcare Appointment", appointment)
	queue_number = cint(doc.name.split("-")[-1]) % 1000 or frappe.db.count(
		"Healthcare Appointment",
		{
			"branch": doc.branch,
			"appointment_date": ["between", [f"{getdate(doc.appointment_date)} 00:00:00", f"{getdate(doc.appointment_date)} 23:59:59"]],
		},
	)
	journey_token = _journey_token(doc.name, doc.patient)
	if frappe.db.has_column("Healthcare Appointment", "journey_token"):
		frappe.db.set_value("Healthcare Appointment", doc.name, "journey_token", journey_token)
	return {
		"appointment_id": doc.name,
		"name": doc.name,
		"patient": doc.patient,
		"patient_display": doc.patient_display,
		"queue_number": queue_number,
		"journey_token": journey_token,
		"qr_token": journey_token,
		"payment_status": doc.payment_status,
		"status": doc.status,
		"practitioner": doc.practitioner,
		"specialty": doc.specialty,
		"appointment_date": str(doc.appointment_date),
	}


@frappe.whitelist()
def verify_journey_token(token: str) -> dict:
	if not token or not token.startswith("JRN-"):
		frappe.throw(_("Invalid journey token."))
	parts = token.split("-", 2)
	if len(parts) < 2:
		frappe.throw(_("Invalid token format."))
	appt = parts[1] if parts[0] == "JRN" else parts[0]
	if not frappe.db.exists("Healthcare Appointment", appt):
		# full token may embed appointment name with dashes
		appt = token[4:].rsplit("-", 1)[0]
	if not frappe.db.exists("Healthcare Appointment", appt):
		frappe.throw(_("Appointment not found."))
	stored = frappe.db.get_value("Healthcare Appointment", appt, "journey_token") if frappe.db.has_column(
		"Healthcare Appointment", "journey_token"
	) else None
	if stored and stored != token:
		frappe.throw(_("Token mismatch."), title=_("Security"))
	return issue_visit_token(appt)


@frappe.whitelist()
def get_cashier_queue(company: str, branch: str) -> list[dict]:
	rows = frappe.get_all(
		"Healthcare Appointment",
		filters={
			"company": company,
			"branch": branch,
			"payment_status": ["in", ["Unpaid", "Partially Paid"]],
			"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]],
			"status": ["not in", ["Cancelled", "No Show"]],
		},
		fields=["name", "patient", "patient_display", "practitioner", "specialty", "booking_fee", "payment_status", "appointment_date"],
		order_by="appointment_date asc",
		limit=100,
	)
	for row in rows:
		row["amount_due"] = flt(row.booking_fee)
	return rows


@frappe.whitelist()
def record_cashier_payment(appointment: str, payment_method: str = "Cash", amount: float | None = None) -> dict:
	doc = frappe.get_doc("Healthcare Appointment", appointment)
	amount = flt(amount or doc.booking_fee)
	doc.payment_status = "Paid" if amount >= flt(doc.booking_fee) else "Partially Paid"
	doc.save(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": doc.patient,
			"company": doc.company,
			"branch": doc.branch,
			"charge_type": "Consultation",
			"description": _("Consultation fee — {0}").format(doc.name),
			"amount": amount,
			"status": "Submitted",
			"reference_doctype": "Healthcare Appointment",
			"reference_name": doc.name,
		}
	).insert(ignore_permissions=True)
	return {"ok": True, "appointment": doc.name, "payment_status": doc.payment_status, "method": payment_method, "amount": amount}


@frappe.whitelist()
def get_physician_workbench(patient: str, encounter: str | None = None) -> dict:
	from omnexa_healthcare.api.patient_chart import get_patient_medical_file

	chart = get_patient_medical_file(patient)
	vitals = {}
	for obs in chart.get("observations") or []:
		profile = (obs.get("observation_profile") or "").lower()
		if profile == "blood_pressure":
			vitals["bp"] = f"{obs.get('value_primary')}/{obs.get('value_secondary')}"
		elif profile in ("heart_rate", "pulse"):
			vitals["hr"] = obs.get("value_primary")
		elif profile in ("body_temperature", "temperature"):
			vitals["temp"] = obs.get("value_primary")
		elif profile == "body_weight":
			vitals["weight"] = obs.get("value_primary")
	chronic = [c.get("clinical_description") for c in (chart.get("conditions") or [])[:3]]
	enc = None
	if encounter:
		enc = frappe.db.get_value("Healthcare Encounter", encounter, ["chief_complaint", "name"], as_dict=True)
	elif chart.get("encounters"):
		enc_name = chart["encounters"][0].get("name")
		enc = frappe.db.get_value("Healthcare Encounter", enc_name, ["chief_complaint", "name"], as_dict=True)
	meds = chart.get("medications") or []
	orders = chart.get("service_requests") or chart.get("lab_orders") or []
	if not orders:
		orders = frappe.get_all(
			"Healthcare Service Request",
			filters={"patient": patient},
			fields=["name", "request_title", "status"],
			limit=10,
			order_by="creation desc",
		)
	return {
		"patient": chart.get("patient"),
		"vitals": vitals,
		"chronic_summary": "; ".join(filter(None, chronic)),
		"diagnosis": enc.get("chief_complaint") if enc else "",
		"medications": meds[:8],
		"orders": orders[:8],
		"referral": "",
		"encounter": enc.get("name") if enc else None,
		"chart": chart,
	}


@frappe.whitelist()
def get_patient_journey_online(company: str, branch: str) -> dict:
	"""Public-safe clinic list for patient self-service (guest via web_booking)."""
	clinics = get_reception_clinics(company, branch)
	return {"clinics": clinics, "steps": 8, "design": "omnexa-journey-v1"}
