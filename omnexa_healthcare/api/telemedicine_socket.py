# -*- coding: utf-8 -*-
"""Realtime telemedicine communication via Frappe publish_realtime + secure chat."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from omnexa_healthcare.api.telemedicine_integration import (
	emit_chat_message,
	emit_device_alert,
	emit_queue_update as publish_queue_update,
	emit_session_event,
)
from omnexa_healthcare.api.telemedicine_security import (
	generate_session_access_token,
	verify_session_access_token,
)


@frappe.whitelist()
def get_socket_config():
	return {
		"success": True,
		"config": {
			"enabled": True,
			"transport": "frappe_realtime",
			"events": [
				"telemedicine_session",
				"telemedicine_queue",
				"telemedicine_chat",
				"telemedicine_device_alert",
			],
			"poll_interval_ms": 5000,
		},
	}


@frappe.whitelist()
def get_socket_auth_token(user=None, session_id=None):
	user = user or frappe.session.user
	token = generate_session_access_token(session_id or "socket", user=user, role="socket")
	return {"success": True, "token": token, "user": user}


@frappe.whitelist()
def validate_socket_token(token, session_id=None):
	try:
		payload = verify_session_access_token(token, session_id=session_id)
		return {"success": True, "user": payload.get("user")}
	except Exception as exc:
		return {"success": False, "error": str(exc)}


@frappe.whitelist()
def send_session_chat_message(session_id, message):
	"""Persist and broadcast an encrypted-at-rest session chat message."""
	try:
		message = (message or "").strip()
		if not message:
			return {"success": False, "error": "Message is required"}

		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
		recipient = _resolve_chat_recipient(session)

		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Secure Message",
				"patient": session.patient,
				"sender": frappe.session.user,
				"recipient": recipient,
				"subject": f"Telemedicine session {session_id}",
				"body": message,
				"thread_id": session_id,
				"company": session.company,
				"branch": session.branch,
			}
		).insert(ignore_permissions=True)

		payload = {
			"id": doc.name,
			"sender": frappe.session.user,
			"sender_name": frappe.utils.get_fullname(frappe.session.user),
			"message": message,
			"timestamp": now_datetime(),
		}
		emit_chat_message(session_id, payload)
		return {"success": True, "message_id": doc.name, "message": payload}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Telemedicine Chat Send Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_session_chat_messages(session_id, limit=50):
	try:
		messages = frappe.get_all(
			"Healthcare Secure Message",
			filters={"thread_id": session_id},
			fields=["name", "sender", "body", "creation"],
			order_by="creation asc",
			limit=int(limit or 50),
		)
		result = []
		for row in messages:
			result.append(
				{
					"id": row.name,
					"sender": row.sender,
					"sender_name": frappe.utils.get_fullname(row.sender) or row.sender,
					"message": row.body,
					"timestamp": row.creation,
				}
			)
		return {"success": True, "messages": result}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Telemedicine Chat Load Error")
		return {"success": False, "error": str(e)}


def _resolve_chat_recipient(session) -> str:
	practitioner_user = frappe.db.get_value("Healthcare Practitioner", session.practitioner, "user")
	if frappe.session.user == practitioner_user:
		return practitioner_user or frappe.session.user
	return practitioner_user or frappe.session.user


@frappe.whitelist()
def emit_queue_update(practitioner, queue_data=None):
	queue_data = frappe.parse_json(queue_data) if isinstance(queue_data, str) else queue_data
	publish_queue_update(practitioner, queue_data)
	return {"success": True}


@frappe.whitelist()
def emit_session_status(session_id, status, data=None):
	data = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	emit_session_event(session_id, status, data)
	return {"success": True}


@frappe.whitelist()
def emit_chat_message_event(session_id, sender, message, timestamp=None):
	payload = {
		"sender": sender,
		"message": message,
		"timestamp": timestamp or now_datetime(),
	}
	emit_chat_message(session_id, payload)
	return {"success": True}


@frappe.whitelist()
def emit_device_alert_event(device_id, alert_level, message, reading_data=None):
	reading_data = frappe.parse_json(reading_data) if isinstance(reading_data, str) else (reading_data or {})
	device = frappe.get_doc("Healthcare Remote Monitoring Device", device_id)
	emit_device_alert(
		device.patient,
		{
			"device_id": device_id,
			"alert_level": alert_level,
			"message": message,
			"reading": reading_data,
		},
	)
	return {"success": True}
