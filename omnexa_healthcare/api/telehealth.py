# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Telehealth video sessions with virtual waiting room."""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.utils import now_datetime

from omnexa_healthcare.api.telehealth_common import build_jitsi_join_url, get_jitsi_server


def _video_enabled() -> bool:
	return bool(frappe.db.get_single_value("Healthcare Settings", "enable_telehealth_video"))


def _room_id(appointment: str) -> str:
	digest = hashlib.sha256(f"omnexa-th-{appointment}".encode()).hexdigest()[:16]
	return f"omnexa-{digest}"


@frappe.whitelist()
def create_telehealth_session(appointment: str) -> dict:
	"""Create or return telehealth session for appointment."""
	if not _video_enabled():
		frappe.throw(_("Telehealth video is disabled."), title=_("Telehealth"))
	if not frappe.db.exists("Healthcare Appointment", appointment):
		frappe.throw(_("Appointment not found."), title=_("Telehealth"))
	appt = frappe.db.get_value(
		"Healthcare Appointment",
		appointment,
		["patient", "practitioner", "company", "branch", "appointment_type"],
		as_dict=True,
	)
	existing = frappe.db.get_value("Healthcare Telehealth Session", {"appointment": appointment}, "name")
	if existing:
		doc = frappe.get_doc("Healthcare Telehealth Session", existing)
	else:
		room = _room_id(appointment)
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Telehealth Session",
				"appointment": appointment,
				"patient": appt.patient,
				"practitioner": appt.practitioner,
				"company": appt.company,
				"branch": appt.branch,
				"room_id": room,
				"join_url": build_jitsi_join_url(room),
				"status": "Scheduled",
				"waiting_room_status": "Not Joined",
			}
		)
		doc.insert(ignore_permissions=True)
	return _session_payload(doc)


@frappe.whitelist()
def get_telehealth_join_url(session: str, role: str = "patient") -> dict:
	"""Return join URL for patient or provider."""
	doc = frappe.get_doc("Healthcare Telehealth Session", session)
	url = build_jitsi_join_url(doc.room_id, display_name=role)
	return {"session": doc.name, "join_url": url, "room_id": doc.room_id, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def join_virtual_waiting_room(session: str, role: str = "patient") -> dict:
	"""Mark participant in virtual waiting room."""
	doc = frappe.get_doc("Healthcare Telehealth Session", session)
	if role == "provider":
		doc.waiting_room_status = "Provider Joined"
		if doc.status == "Scheduled":
			doc.status = "Waiting"
	else:
		doc.waiting_room_status = "Patient Waiting"
	doc.save(ignore_permissions=True)
	return {
		"session": doc.name,
		"waiting_room_status": doc.waiting_room_status,
		"join_url": build_jitsi_join_url(doc.room_id, display_name=role),
		"jitsi_server": get_jitsi_server(),
	}


@frappe.whitelist()
def start_telehealth_session(session: str) -> dict:
	doc = frappe.get_doc("Healthcare Telehealth Session", session)
	doc.status = "In Progress"
	doc.waiting_room_status = "In Session"
	doc.started_at = now_datetime()
	doc.save(ignore_permissions=True)
	return _session_payload(doc)


@frappe.whitelist()
def end_telehealth_session(session: str) -> dict:
	doc = frappe.get_doc("Healthcare Telehealth Session", session)
	doc.status = "Completed"
	doc.ended_at = now_datetime()
	doc.save(ignore_permissions=True)
	return _session_payload(doc)


def _session_payload(doc) -> dict:
	return {
		"name": doc.name,
		"appointment": doc.appointment,
		"patient": doc.patient,
		"practitioner": doc.practitioner,
		"room_id": doc.room_id,
		"join_url": doc.join_url,
		"status": doc.status,
		"waiting_room_status": doc.waiting_room_status,
		"jitsi_server": get_jitsi_server(),
	}
