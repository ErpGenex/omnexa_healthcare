# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Omnexa Journey Desk — unified APIs for Reception · Cashier · Physician · Patient."""

from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64encode
from io import BytesIO

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, today

from omnexa_healthcare.api.patient_registration import assert_booking_allowed, register_patient_full
from omnexa_healthcare.api.scheduling import create_healthcare_appointment
from omnexa_healthcare.scheduling_engine import get_available_slots


def _patient_search_fields() -> list[str]:
	return [f for f in ["name", "full_name", "gender", "birth_date", "branch"] if frappe.db.has_column("Healthcare Patient", f)]


def _patient_search_row(patient: dict, match_type: str, match_value: str) -> dict:
	display = patient.get("full_name") or ""
	return {**patient, "patient_name": display, "match_type": match_type, "match_value": match_value}


def _journey_token(appointment: str, patient: str) -> str:
	secret = frappe.get_site_config().get("secret_key") or "omnexa-journey"
	raw = json.dumps({"appt": appointment, "patient": patient, "ts": str(now_datetime())}, sort_keys=True)
	sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:24]
	return f"JRN-{appointment}-{sig}"


def _qr_data_uri(payload: str) -> str | None:
	text = (payload or "").strip()
	if not text:
		return None
	try:
		from pyqrcode import create as qrcreate
	except Exception:
		return None
	url = qrcreate(text)
	stream = BytesIO()
	try:
		url.svg(stream, scale=5, background="#ffffff", module_color="#003366")
		svg = stream.getvalue().decode().replace("\n", "")
	finally:
		stream.close()
	return f"data:image/svg+xml;base64,{b64encode(svg.encode()).decode()}"


def _patient_mobile(patient: str) -> str:
	system_field = "contact_system" if frappe.db.has_column("Healthcare Patient Telecom", "contact_system") else "system"
	for system in ("mobile", "phone", "sms"):
		filters = {"parent": patient, system_field: system}
		value = frappe.db.get_value(
			"Healthcare Patient Telecom",
			filters,
			"value",
			order_by="rank asc",
		)
		if value:
			return value
	# Any phone-like value
	rows = frappe.get_all(
		"Healthcare Patient Telecom",
		filters={"parent": patient},
		fields=["value"],
		order_by="rank asc",
		limit=3,
	)
	return rows[0].value if rows else ""


def _visit_token_context(appointment: str) -> dict:
	if not frappe.db.exists("Healthcare Appointment", appointment):
		frappe.throw(_("Appointment not found."))
	doc = frappe.get_doc("Healthcare Appointment", appointment)
	token = ""
	if frappe.db.has_column("Healthcare Appointment", "journey_token"):
		token = doc.journey_token or ""
	if not token:
		token = _journey_token(doc.name, doc.patient)
	qr_payload = token or doc.name
	queue_number = cint(str(doc.name).split("-")[-1]) % 1000 or 0
	return {
		"appointment": doc.name,
		"appointment_id": doc.name,
		"patient": doc.patient,
		"patient_display": doc.patient_display or doc.patient,
		"practitioner": doc.practitioner,
		"specialty": doc.specialty,
		"appointment_date": str(doc.appointment_date or ""),
		"payment_status": doc.payment_status,
		"status": doc.status,
		"queue_number": queue_number,
		"journey_token": token,
		"qr_token": token,
		"qr_data_uri": _qr_data_uri(qr_payload),
		"patient_phone": _patient_mobile(doc.patient),
		"company": doc.company,
		"branch": doc.branch,
	}


def _visit_token_print_html(ctx: dict) -> str:
	qr_img = f'<img src="{ctx["qr_data_uri"]}" alt="QR" width="160" height="160" />' if ctx.get("qr_data_uri") else ""
	return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{frappe.utils.escape_html(ctx["appointment"])}</title>
	<style>
	body{{font-family:Arial,sans-serif;text-align:center;padding:24px;color:#003366}}
	.card{{max-width:360px;margin:0 auto;border:2px solid #003366;border-radius:12px;padding:20px}}
	h1{{font-size:18px;margin:0 0 8px}} .id{{font-size:20px;font-weight:800}} .muted{{color:#64748b}}
	</style></head><body><div class="card">
	<h1>{_("Visit Token")}</h1>
	<div class="id">{frappe.utils.escape_html(ctx["appointment"])}</div>
	<p>{_("Queue")}: <strong>{ctx["queue_number"]}</strong></p>
	<p>{frappe.utils.escape_html(ctx["patient_display"])}</p>
	<p class="muted">{frappe.utils.escape_html(ctx["appointment_date"])}</p>
	{qr_img}
	<p>{frappe.utils.escape_html(ctx.get("payment_status") or "")}</p>
	<p class="muted" style="font-size:11px">{frappe.utils.escape_html(ctx.get("journey_token") or "")}</p>
	</div></body></html>"""


@frappe.whitelist()
def get_visit_token_qr(payload: str) -> dict:
	return {"data_uri": _qr_data_uri(payload)}


@frappe.whitelist()
def get_visit_token_details(appointment: str) -> dict:
	return _visit_token_context(appointment)


@frappe.whitelist()
def get_visit_token_share(appointment: str) -> dict:
	ctx = _visit_token_context(appointment)
	message = _("Visit token {0} — Queue {1} — {2} — Ref: {3}").format(
		ctx["appointment"],
		ctx["queue_number"],
		ctx["patient_display"],
		ctx["journey_token"] or ctx["appointment"],
	)
	phone = (ctx.get("patient_phone") or "").replace(" ", "").replace("+", "")
	if phone.startswith("0"):
		phone = f"20{phone[1:]}"
	return {"phone": phone, "message": message}


@frappe.whitelist()
def download_visit_token_pdf(appointment: str):
	ctx = _visit_token_context(appointment)
	html = _visit_token_print_html(ctx)
	from frappe.utils.pdf import get_pdf

	frappe.local.response.filename = f"{appointment}-token.pdf"
	frappe.local.response.filecontent = get_pdf(html)
	frappe.local.response.type = "pdf"


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
			_patient_search_fields(),
			as_dict=True,
		)
		if p and (not branch or p.branch == branch):
			results.append(_patient_search_row(p, id_row.identifier_type, id_row.value))
	# Telecom
	for tel in frappe.get_all(
		"Healthcare Patient Telecom",
		filters={"value": ["like", f"%{q}%"]},
		fields=["parent", "value"],
		limit=10,
	):
		if any(r["name"] == tel.parent for r in results):
			continue
		p = frappe.db.get_value("Healthcare Patient", tel.parent, _patient_search_fields(), as_dict=True)
		if p and (not branch or p.branch == branch):
			results.append(_patient_search_row(p, "Mobile", tel.value))
	# Name
	if len(q) >= 3:
		or_filters = []
		for field in ("full_name", "given_name", "family_name"):
			if frappe.db.has_column("Healthcare Patient", field):
				or_filters.append([field, "like", f"%{q}%"])
		name_filters = {**({"branch": branch} if branch else {})}
		for p in frappe.get_all(
			"Healthcare Patient",
			filters=name_filters,
			or_filters=or_filters or None,
			fields=_patient_search_fields(),
			limit=10,
		) if or_filters else []:
			if not any(r["name"] == p.name for r in results):
				results.append(_patient_search_row(p, "Name", p.get("full_name") or q))
	return results[:15]


@frappe.whitelist()
def get_reception_today_appointments(company: str | None = None, branch: str | None = None) -> list[dict]:
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	filters: dict = {
		"appointment_date": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]],
		"status": ["not in", ["Cancelled"]],
	}
	if branch:
		filters["branch"] = branch
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Healthcare Appointment",
		filters=filters,
		fields=[
			"name",
			"patient",
			"patient_display",
			"practitioner",
			"specialty",
			"appointment_date",
			"status",
			"payment_status",
			"booking_fee",
		],
		order_by="appointment_date asc",
		limit=50,
	)


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
				"slot_end": slot_end,
				"appointment_type": appointment_type,
				"booking_fee": flt(booking_fee),
				"payment_status": "Unpaid",
				"booking_channel": "Desk",
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
		"qr_data_uri": _qr_data_uri(journey_token),
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
	charge_name = doc.service_charge or _create_cashier_service_charge(doc, amount)
	if not doc.service_charge:
		doc.db_set("service_charge", charge_name, update_modified=False)
	doc.payment_status = "Paid" if amount >= flt(doc.booking_fee) else "Partially Paid"
	doc.save(ignore_permissions=True)
	return {
		"ok": True,
		"appointment": doc.name,
		"service_charge": charge_name,
		"payment_status": doc.payment_status,
		"method": payment_method,
		"amount": amount,
	}


def _fallback_billing_item(company: str) -> str | None:
	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER

	for code in (f"{DEMO_MARKER}OPD-SVC",):
		name = frappe.db.get_value("Item", {"item_code": code, "company": company}, "name")
		if name:
			return name
	return frappe.db.get_value(
		"Item",
		{"company": company, "is_sales_item": 1, "disabled": 0},
		"name",
		order_by="modified desc",
	)


def _create_cashier_service_charge(appt, amount: float) -> str:
	from omnexa_healthcare.api.billing_automation import _resolve_appointment_fee
	from omnexa_healthcare.patient_billing import ensure_patient_billing_account

	billing_customer = ensure_patient_billing_account(appt.patient) or frappe.db.get_value(
		"Healthcare Patient", appt.patient, "billing_customer"
	)
	if not billing_customer:
		frappe.throw(_("Patient billing account could not be resolved."), title=_("Billing"))

	item, rate = _resolve_appointment_fee(appt)
	line_rate = flt(amount) or flt(rate) or flt(appt.booking_fee)
	if not item:
		item = _fallback_billing_item(appt.company)

	line: dict = {
		"qty": 1,
		"rate": line_rate,
		"description": _("Consultation fee — {0}").format(appt.name),
	}
	if item:
		line["item"] = item

	charge = frappe.get_doc(
		{
			"doctype": "Healthcare Service Charge",
			"patient": appt.patient,
			"billing_customer": billing_customer,
			"company": appt.company,
			"branch": appt.branch,
			"posting_date": getdate(appt.appointment_date or today()),
			"status": "Draft",
			"items": [line],
		}
	)
	charge.insert(ignore_permissions=True)
	return charge.name


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
