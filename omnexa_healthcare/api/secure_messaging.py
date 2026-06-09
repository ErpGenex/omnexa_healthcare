# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""HIPAA-style secure messaging between care team and patients."""

from __future__ import annotations

import uuid

import frappe
from frappe import _


@frappe.whitelist()
def send_secure_message(
	recipient: str,
	body: str,
	patient: str,
	subject: str | None = None,
	thread_id: str | None = None,
) -> dict:
	if not (recipient and body and patient):
		frappe.throw(_("recipient, body and patient are required"))
	company = frappe.db.get_value("Healthcare Patient", patient, "company")
	branch = frappe.db.get_value("Healthcare Patient", patient, "branch")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Secure Message",
			"patient": patient,
			"sender": frappe.session.user,
			"recipient": recipient,
			"subject": subject or _("Secure message"),
			"body": body,
			"thread_id": thread_id or str(uuid.uuid4())[:12],
			"company": company,
			"branch": branch,
		}
	).insert()
	return {"name": doc.name, "thread_id": doc.thread_id}


@frappe.whitelist()
def get_message_thread(thread_id: str) -> list[dict]:
	user = frappe.session.user
	return frappe.get_all(
		"Healthcare Secure Message",
		filters={"thread_id": thread_id},
		or_filters=[["sender", "=", user], ["recipient", "=", user]],
		fields=["name", "sender", "recipient", "subject", "body", "is_read", "creation"],
		order_by="creation asc",
	)


@frappe.whitelist()
def mark_messages_read(thread_id: str) -> dict:
	user = frappe.session.user
	for name in frappe.get_all(
		"Healthcare Secure Message",
		filters={"thread_id": thread_id, "recipient": user, "is_read": 0},
		pluck="name",
	):
		frappe.db.set_value("Healthcare Secure Message", name, "is_read", 1)
	return {"thread_id": thread_id, "marked_read": True}
