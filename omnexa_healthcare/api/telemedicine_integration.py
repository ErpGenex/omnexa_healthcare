# -*- coding: utf-8 -*-
"""World-class telemedicine integrations: FHIR, billing, e-Rx, realtime."""

from __future__ import annotations

import frappe
from frappe.utils import flt, get_datetime, now_datetime, today

from omnexa_healthcare.api.telemedicine_security import generate_session_access_token
from omnexa_healthcare.patient_billing import ensure_patient_billing_account


def finalize_completed_session(session):
	"""Run post-completion integrations once per session."""
	session = frappe.get_doc("Healthcare Telemedicine Session", session.name)
	if frappe.db.get_value("Healthcare Telemedicine Session", session.name, "encounter"):
		return

	encounter_name = create_encounter_from_session(session)
	if encounter_name:
		frappe.db.set_value(
			"Healthcare Telemedicine Session",
			session.name,
			"encounter",
			encounter_name,
			update_modified=False,
		)
		session.encounter = encounter_name

	service_charge_name = create_service_charge_from_session(session, encounter_name)
	if service_charge_name:
		frappe.db.set_value(
			"Healthcare Telemedicine Session",
			session.name,
			"service_charge",
			service_charge_name,
			update_modified=False,
		)
		session.service_charge = service_charge_name

	medication_request_name = create_medication_request_from_session(session, encounter_name)
	if medication_request_name:
		frappe.db.set_value(
			"Healthcare Telemedicine Session",
			session.name,
			"medication_request",
			medication_request_name,
			update_modified=False,
		)
		session.medication_request = medication_request_name

	emit_session_event(session.name, "session_completed", {
		"encounter": encounter_name,
		"service_charge": service_charge_name,
		"medication_request": medication_request_name,
	})


def create_encounter_from_session(session) -> str | None:
	try:
		period_start = session.start_datetime or session.scheduled_datetime or now_datetime()
		period_end = session.end_datetime or now_datetime()

		encounter = frappe.get_doc(
			{
				"doctype": "Healthcare Encounter",
				"naming_series": "ENC-.#####",
				"patient": session.patient,
				"practitioner": session.practitioner,
				"appointment": session.appointment,
				"company": session.company,
				"branch": session.branch,
				"encounter_class": "virtual",
				"encounter_type": "Telehealth",
				"encounter_priority": "routine",
				"status": "finished",
				"period_start": period_start,
				"period_end": period_end,
				"chief_complaint": session.clinical_notes or "Telemedicine consultation",
			}
		)

		if session.diagnosis:
			condition = frappe.db.get_value(
				"Healthcare Clinical Condition",
				session.diagnosis,
				["description", "icd10_code"],
				as_dict=True,
			)
			if condition:
				encounter.append(
					"diagnoses",
					{
						"description": condition.description or session.diagnosis,
						"icd10_code": condition.icd10_code,
					},
				)

		encounter.insert(ignore_permissions=True)
		return encounter.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Create Encounter from Telemedicine Session")
		return None


def _resolve_telemedicine_billing_item(company: str) -> tuple[str | None, float]:
	item_name = frappe.db.get_value(
		"Item",
		{"company": company, "is_sales_item": 1, "disabled": 0, "item_name": ["like", "%Telemedicine%"]},
		"name",
	)
	if not item_name:
		items = frappe.get_all(
			"Item",
			filters={"company": company, "is_sales_item": 1, "disabled": 0},
			fields=["name"],
			order_by="modified desc",
			limit=1,
		)
		item_name = items[0].name if items else None
	rate = 350.0
	if item_name:
		item_rate = frappe.db.get_value("Item Price", {"item_code": frappe.db.get_value("Item", item_name, "item_code"), "selling": 1}, "price_list_rate")
		if item_rate:
			rate = flt(item_rate)
	return item_name, rate


def create_service_charge_from_session(session, encounter_name: str | None) -> str | None:
	try:
		if frappe.db.get_value("Healthcare Telemedicine Session", session.name, "service_charge"):
			return frappe.db.get_value("Healthcare Telemedicine Session", session.name, "service_charge")

		billing_customer = ensure_patient_billing_account(session.patient)
		if not billing_customer:
			billing_customer = frappe.db.get_value("Healthcare Patient", session.patient, "billing_customer")
		if not billing_customer:
			return None

		item_name, rate = _resolve_telemedicine_billing_item(session.company)
		if not item_name:
			return None

		consultation_fee = frappe.db.get_value(
			"Healthcare Practitioner Branch",
			{"parent": session.practitioner, "branch": session.branch, "is_active": 1},
			"consultation_fee",
		)
		if consultation_fee:
			rate = flt(consultation_fee)

		charge = frappe.get_doc(
			{
				"doctype": "Healthcare Service Charge",
				"naming_series": "HSC-.#####",
				"patient": session.patient,
				"billing_customer": billing_customer,
				"company": session.company,
				"branch": session.branch,
				"encounter": encounter_name,
				"posting_date": today(),
				"status": "Draft",
				"items": [
					{
						"description": f"Telemedicine consultation — {session.name}",
						"practitioner": session.practitioner,
						"service_category": "Consultation",
						"item": item_name,
						"qty": 1,
						"rate": rate,
					}
				],
			}
		)
		charge.insert(ignore_permissions=True)
		return charge.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Create Service Charge from Telemedicine Session")
		return None


def create_medication_request_from_session(session, encounter_name: str | None) -> str | None:
	if not session.get("prescriptions"):
		return None

	try:
		if frappe.db.get_value("Healthcare Telemedicine Session", session.name, "medication_request"):
			return frappe.db.get_value("Healthcare Telemedicine Session", session.name, "medication_request")

		diagnosis_text = session.clinical_notes or "Telemedicine consultation"
		if session.diagnosis:
			desc = frappe.db.get_value("Healthcare Clinical Condition", session.diagnosis, "description")
			if desc:
				diagnosis_text = desc

		med_request = frappe.get_doc(
			{
				"doctype": "Healthcare Medication Request",
				"naming_series": "HMR-.#####",
				"patient": session.patient,
				"practitioner": session.practitioner,
				"encounter": encounter_name,
				"diagnosis": diagnosis_text,
				"company": session.company,
				"branch": session.branch,
				"status": "Draft",
				"items": [],
			}
		)

		for row in session.prescriptions:
			drug_name = row.medication
			if frappe.db.exists("Healthcare Drug Formulary", row.medication):
				drug_name = frappe.db.get_value("Healthcare Drug Formulary", row.medication, "drug_name") or row.medication
			med_request.append(
				"items",
				{
					"drug_name": drug_name,
					"formulary_item": row.medication if frappe.db.exists("Healthcare Drug Formulary", row.medication) else None,
					"dose": row.dosage,
					"frequency": row.frequency,
					"duration_days": _parse_duration_days(row.duration),
					"instructions": row.instructions,
				},
			)

		med_request.insert(ignore_permissions=True)
		return med_request.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Create Medication Request from Telemedicine Session")
		return None


def _parse_duration_days(duration: str | None) -> int | None:
	if not duration:
		return None
	duration = str(duration).strip().lower()
	for token in duration.replace("days", "").replace("day", "").split():
		if token.isdigit():
			return int(token)
	return None


def build_telemedicine_fhir_bundle(session_id: str) -> dict:
	from omnexa_healthcare.api.fhir_export import get_fhir_encounter, get_fhir_medication_request, get_fhir_patient
	from omnexa_healthcare.api.telemedicine_monitoring import get_patient_readings

	session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
	entries = []

	patient_resource = get_fhir_patient(session.patient)
	entries.append({"fullUrl": f"Patient/{session.patient}", "resource": patient_resource})

	encounter_name = session.encounter or frappe.db.get_value(
		"Healthcare Telemedicine Session", session_id, "encounter"
	)
	if encounter_name:
		entries.append({"fullUrl": f"Encounter/{encounter_name}", "resource": get_fhir_encounter(encounter_name)})

	med_request = session.medication_request or frappe.db.get_value(
		"Healthcare Telemedicine Session", session_id, "medication_request"
	)
	if med_request:
		entries.append(
			{
				"fullUrl": f"MedicationRequest/{med_request}",
				"resource": get_fhir_medication_request(med_request),
			}
		)

	readings_result = get_patient_readings(session.patient)
	for reading in (readings_result.get("readings") or [])[:5]:
		reading_name = reading.get("name") if isinstance(reading, dict) else reading.name
		metric_type = reading.get("metric_type") if isinstance(reading, dict) else reading.metric_type
		reading_datetime = reading.get("reading_datetime") if isinstance(reading, dict) else reading.reading_datetime
		value = reading.get("value") if isinstance(reading, dict) else reading.value
		unit = reading.get("unit") if isinstance(reading, dict) else reading.unit
		entries.append(
			{
				"fullUrl": f"Observation/{reading_name}",
				"resource": {
					"resourceType": "Observation",
					"id": reading_name,
					"status": "final",
					"code": {"text": metric_type},
					"subject": {"reference": f"Patient/{session.patient}"},
					"effectiveDateTime": str(reading_datetime),
					"valueQuantity": {"value": value, "unit": unit},
				},
			}
		)

	return {
		"resourceType": "Bundle",
		"type": "collection",
		"timestamp": now_datetime().isoformat(),
		"entry": entries,
	}


def emit_session_event(session_id: str, event: str, data: dict | None = None):
	"""Publish realtime updates to session participants and queue subscribers."""
	payload = {"session_id": session_id, "event": event, "data": data or {}}
	frappe.publish_realtime("telemedicine_session", payload, room=session_id, after_commit=True)

	session = frappe.db.get_value(
		"Healthcare Telemedicine Session",
		session_id,
		["practitioner", "patient"],
		as_dict=True,
	)
	if session and session.practitioner:
		frappe.publish_realtime(
			"telemedicine_queue",
			payload,
			user=_practitioner_user(session.practitioner),
			after_commit=True,
		)


def emit_queue_update(practitioner_id: str, queue_data: dict | list | None = None):
	frappe.publish_realtime(
		"telemedicine_queue",
		{"practitioner": practitioner_id, "queue": queue_data or []},
		user=_practitioner_user(practitioner_id),
		after_commit=True,
	)


def emit_chat_message(session_id: str, message: dict):
	frappe.publish_realtime(
		"telemedicine_chat",
		{"session_id": session_id, "message": message},
		room=session_id,
		after_commit=True,
	)


def emit_device_alert(patient_id: str, alert: dict):
	frappe.publish_realtime(
		"telemedicine_device_alert",
		{"patient": patient_id, "alert": alert},
		after_commit=True,
	)


def _practitioner_user(practitioner_id: str) -> str | None:
	return frappe.db.get_value("Healthcare Practitioner", practitioner_id, "user")


def build_join_payload(session_id: str, user_type: str = "participant") -> dict:
	session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
	token = generate_session_access_token(session_id, role=user_type)
	from omnexa_healthcare.api.telemedicine_video import get_jitsi_meeting_config

	jitsi = get_jitsi_meeting_config(session_id, user_type=user_type)
	return {
		"success": True,
		"room_id": session.room_id,
		"token": token,
		"session_type": session.session_type,
		"recording_enabled": session.recording_enabled,
		"jitsi": jitsi,
	}
