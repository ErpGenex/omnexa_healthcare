# -*- coding: utf-8 -*-
import frappe
from frappe import _
import uuid

from omnexa_healthcare.api.telemedicine_security import generate_jitsi_jwt, generate_session_access_token


def _get_telemedicine_config():
	from omnexa_healthcare.api.telemedicine_admin import ensure_telemedicine_configuration

	return ensure_telemedicine_configuration()


@frappe.whitelist()
def create_video_room(session_id):
	"""Create WebRTC room for telemedicine session"""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if session.room_id:
			return {"success": True, "room_id": session.room_id, "existing": True}

		room_id = f"tele_{uuid.uuid4().hex[:12]}"
		session.room_id = room_id
		session.save()

		return {
			"success": True,
			"room_id": room_id,
			"existing": False,
			"session_type": session.session_type,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Room Creation Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_video_token(session_id, user_type):
	"""Generate secure JWT token for video session access."""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if session.status not in ["Scheduled", "In Progress"]:
			return {"success": False, "error": "Session not available"}

		token = generate_session_access_token(session_id, role=user_type or "participant")
		return {
			"success": True,
			"token": token,
			"room_id": session.room_id,
			"session_type": session.session_type,
			"recording_enabled": session.recording_enabled,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Token Generation Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_jitsi_meeting_config(session_id, user_type="participant"):
	"""Return Jitsi External API configuration for a telemedicine session."""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
		config = _get_telemedicine_config()
		domain = (config.jitsi_domain or "meet.jit.si").strip()
		display_name = frappe.utils.get_fullname(frappe.session.user) or frappe.session.user
		is_moderator = user_type in ("doctor", "practitioner", "moderator")

		if session.practitioner and frappe.db.get_value("Healthcare Practitioner", session.practitioner, "user") == frappe.session.user:
			is_moderator = True

		jwt_token = generate_jitsi_jwt(session.room_id, display_name, is_moderator=is_moderator)
		ice_servers = []
		if config.stun_server_url:
			ice_servers.append({"urls": config.stun_server_url})
		if config.turn_server_url:
			entry = {"urls": config.turn_server_url}
			if config.turn_username:
				entry["username"] = config.turn_username
			if config.turn_credential:
				entry["credential"] = config.turn_credential
			ice_servers.append(entry)

		return {
			"success": True,
			"domain": domain,
			"room_name": session.room_id,
			"jwt": jwt_token,
			"display_name": display_name,
			"is_moderator": is_moderator,
			"ice_servers": ice_servers,
			"recording_enabled": bool(session.recording_enabled),
			"config_overwrite": {
				"startWithAudioMuted": False,
				"startWithVideoMuted": session.session_type == "Voice",
				"disableChat": session.session_type == "Video",
			},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Jitsi Meeting Config Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def end_video_room(session_id):
	"""Close WebRTC room"""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if session.status == "In Progress":
			return {"success": False, "error": "Session still in progress"}

		return {"success": True}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Room End Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_video_recording(session_id):
	"""Get video recording URL"""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if not session.recording_enabled or not session.recording_url:
			return {"success": False, "error": "No recording available"}

		return {
			"success": True,
			"recording_url": session.recording_url,
			"expiry": session.recording_expiry,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Recording Get Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def delete_video_recording(session_id):
	"""Delete video recording"""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if not session.recording_url:
			return {"success": False, "error": "No recording to delete"}

		session.recording_url = None
		session.recording_expiry = None
		session.save()

		return {"success": True}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Recording Delete Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def enable_recording(session_id):
	"""Enable recording for session"""
	try:
		session = frappe.get_doc("Healthcare Telemedicine Session", session_id)

		if session.status == "Completed":
			return {"success": False, "error": "Cannot enable recording for completed session"}

		config = _get_telemedicine_config()
		if not config.allow_recording:
			return {"success": False, "error": "Recording not allowed by configuration"}

		session.recording_enabled = 1
		session.save()

		return {"success": True, "recording_enabled": True}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Recording Enable Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_video_servers_config():
	"""Get video server configuration"""
	try:
		from omnexa_healthcare.api.telemedicine_admin import get_config

		config_result = get_config()

		if config_result.get("success") and config_result.get("config"):
			config = config_result["config"]
			return {
				"success": True,
				"jitsi_domain": config.get("jitsi_domain") or "meet.jit.si",
				"jitsi_app_id": config.get("jitsi_app_id"),
				"turn_server_url": config.get("turn_server_url"),
				"stun_server_url": config.get("stun_server_url"),
				"video_quality": config.get("video_quality"),
			}
		return {"success": False, "error": "Configuration not found"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Video Config Get Error")
		return {"success": False, "error": str(e)}
