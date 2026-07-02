# -*- coding: utf-8 -*-
"""Fix Healthcare Telemedicine Configuration Single DocType and canonical row."""

import frappe

CANONICAL = "Healthcare Telemedicine Configuration"

DEFAULTS = {
	"enable_video_consultations": 1,
	"enable_voice_consultations": 1,
	"enable_chat_consultations": 1,
	"default_session_duration": 30,
	"max_session_duration": 60,
	"enable_waitlist": 1,
	"max_concurrent_sessions": 50,
	"allow_recording": 0,
	"auto_record": 0,
	"recording_retention_days": 30,
	"enable_screen_sharing": 1,
	"enable_whiteboard": 1,
	"enable_file_sharing": 1,
	"max_file_size_mb": 10,
	"allowed_file_types": "pdf,jpg,jpeg,png,doc,docx",
	"video_quality": "HD",
	"enable_ai_transcription": 0,
	"enable_ai_summarization": 0,
	"stun_server_url": "stun:stun.l.google.com:19302",
	"jitsi_domain": "meet.jit.si",
	"session_timeout_minutes": 15,
}


def execute():
	# DocType JSON says Single but DB was issingle=0, causing orphan rows + load failures.
	frappe.db.set_value("DocType", CANONICAL, "issingle", 1)
	frappe.clear_cache(doctype=CANONICAL)

	existing = frappe.db.sql(
		f"SELECT * FROM `tab{CANONICAL}` ORDER BY modified DESC LIMIT 1",
		as_dict=True,
	)
	row = existing[0] if existing else {}

	frappe.db.sql(f"DELETE FROM `tab{CANONICAL}`")
	frappe.db.sql("DELETE FROM `tabSingles` WHERE doctype=%s", CANONICAL)

	doc = frappe.new_doc(CANONICAL)
	for key, value in DEFAULTS.items():
		doc.set(key, row.get(key) if row.get(key) not in (None, "") else value)
	if row.get("jitsi_app_id"):
		doc.jitsi_app_id = row.get("jitsi_app_id")
	if row.get("jitsi_secret"):
		doc.jitsi_secret = row.get("jitsi_secret")
	if row.get("turn_server_url"):
		doc.turn_server_url = row.get("turn_server_url")
	if row.get("turn_username"):
		doc.turn_username = row.get("turn_username")
	if row.get("turn_credential"):
		doc.turn_credential = row.get("turn_credential")

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=CANONICAL)
