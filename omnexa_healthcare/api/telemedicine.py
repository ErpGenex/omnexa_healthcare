# -*- coding: utf-8 -*-
import frappe
from frappe import _
import json
import uuid
from datetime import datetime, timedelta
from frappe.utils import now, now_datetime, get_datetime, time_diff_in_seconds


def _normalize_session_type(session_type):
    mapping = {
        "video": "Video",
        "voice": "Voice",
        "chat": "Chat",
    }
    if not session_type:
        return "Video"
    return mapping.get(str(session_type).lower(), session_type)


SPECIALTY_SLUG_MAP = {
	"general": ("GEN", "General Medicine"),
	"cardiology": ("CAR", "Cardiology"),
	"dermatology": ("DER", "Dermatology"),
	"pediatrics": ("PED", "Pediatrics"),
	"gynecology": ("GYNECOLOGY", "Gynecology"),
	"orthopedics": ("ORTHO", "Orthopedics"),
	"neurology": ("NEUROLOGY", "Neurology"),
	"psychiatry": ("PSYCH", "Psychiatry"),
	"ophthalmology": ("OPHTHALMOLOG", "Ophthalmology"),
	"ent": ("ENT", "ENT"),
	"gastroenterology": ("GASTROENTERO", "Gastroenterology"),
	"endocrinology": ("ENDO", "Endocrinology"),
}


def _resolve_specialty_filter(specialty: str | None) -> str | None:
	if not specialty:
		return None
	raw = specialty.strip()
	if frappe.db.exists("Healthcare Specialty", raw):
		return raw
	key = raw.lower()
	if key in SPECIALTY_SLUG_MAP:
		for candidate in SPECIALTY_SLUG_MAP[key]:
			name = frappe.db.get_value("Healthcare Specialty", candidate, "name")
			if name:
				return name
			name = frappe.db.get_value("Healthcare Specialty", {"specialty_name": candidate}, "name")
			if name:
				return name
	return frappe.db.get_value(
		"Healthcare Specialty",
		{"specialty_name": ["like", f"%{raw}%"]},
		"name",
	)


def _resolve_practitioner_context(practitioner_id):
    practitioner = frappe.get_doc("Healthcare Practitioner", practitioner_id)
    branch = practitioner.branch_assignments[0].branch if practitioner.branch_assignments else None
    if not branch:
        branch = frappe.db.get_value("Branch", {"company": practitioner.company}, "name")
    return practitioner.company, branch


@frappe.whitelist()
def create_telemedicine_session(data):
    """Create a new telemedicine session"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        # Generate room ID
        room_id = f"tele_{uuid.uuid4().hex[:12]}"
        session_type = _normalize_session_type(data.get("session_type", "Video"))
        scheduled_datetime = data.get("scheduled_datetime") or now_datetime()
        company = data.get("company")
        branch = data.get("branch")
        if data.get("practitioner") and (not company or not branch):
            company, branch = _resolve_practitioner_context(data.get("practitioner"))
        
        # Create session
        session = frappe.get_doc({
            "doctype": "Healthcare Telemedicine Session",
            "patient": data.get("patient"),
            "practitioner": data.get("practitioner"),
            "appointment": data.get("appointment"),
            "session_type": session_type,
            "scheduled_datetime": scheduled_datetime,
            "company": company,
            "branch": branch,
            "room_id": room_id,
            "status": "Scheduled",
            "clinical_notes": data.get("clinical_notes") or data.get("notes"),
        })
        
        session.insert(ignore_permissions=bool(data.get("portal_booking")))

        # Create queue entry
        queue = frappe.get_doc({
            "doctype": "Healthcare Telemedicine Queue",
            "practitioner": data.get("practitioner"),
            "session": session.name,
            "queue_position": get_next_queue_position(data.get("practitioner")),
            "status": "Waiting",
            "joined_datetime": now(),
            "company": company,
            "branch": branch
        })
        queue.insert(ignore_permissions=bool(data.get("portal_booking")))
        
        return {
            "success": True,
            "session_id": session.name,
            "room_id": room_id,
            "status": session.status
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session Creation Error")
        return {"success": False, "error": str(e) or frappe.get_traceback().splitlines()[-1]}


@frappe.whitelist()
def start_telemedicine_session(session_id):
    """Start a telemedicine session"""
    try:
        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        
        if session.status != "Scheduled":
            return {"success": False, "error": "Session is not in Scheduled status"}
        
        session.status = "In Progress"
        session.start_datetime = now()
        session.save()
        
        # Update queue
        queue_entries = frappe.get_all(
            "Healthcare Telemedicine Queue",
            filters={"session": session_id, "status": "Waiting"},
        )
        
        for entry in queue_entries:
            queue = frappe.get_doc("Healthcare Telemedicine Queue", entry.name)
            queue.status = "In Progress"
            queue.start_datetime = now()
            queue.save()
        
        from omnexa_healthcare.api.telemedicine_integration import emit_session_event

        emit_session_event(session_id, "session_started", {"status": session.status})
        
        return {"success": True, "status": session.status}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session Start Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def end_telemedicine_session(session_id, data):
    """End a telemedicine session"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        
        if session.status != "In Progress":
            return {"success": False, "error": "Session is not in In Progress status"}
        
        session.status = "Completed"
        session.end_datetime = now()
        
        # Calculate duration
        if session.start_datetime and session.end_datetime:
            session.duration_minutes = int(
                time_diff_in_seconds(
                    get_datetime(session.end_datetime),
                    get_datetime(session.start_datetime),
                ) / 60
            )
        
        # Update clinical data
        if data.get("diagnosis"):
            session.diagnosis = data.get("diagnosis")
        if data.get("clinical_notes"):
            session.clinical_notes = data.get("clinical_notes")
        if data.get("technical_quality"):
            session.technical_quality = data.get("technical_quality")
        if data.get("connection_issues"):
            session.connection_issues = data.get("connection_issues")
        if data.get("rating"):
            session.rating = data.get("rating")
        if data.get("patient_feedback"):
            session.patient_feedback = data.get("patient_feedback")
        
        session.save()
        
        # Update queue
        queue_entries = frappe.get_all(
            "Healthcare Telemedicine Queue",
            filters={"session": session_id},
        )
        
        for entry in queue_entries:
            queue = frappe.get_doc("Healthcare Telemedicine Queue", entry.name)
            queue.status = "Completed"
            queue.end_datetime = frappe.utils.now()
            queue.save()
        
        from omnexa_healthcare.api.telemedicine_integration import finalize_completed_session, emit_session_event

        finalize_completed_session(session)
        emit_session_event(session_id, "session_completed", {
            "status": session.status,
            "duration": session.duration_minutes,
        })
        
        return {"success": True, "status": session.status, "duration": session.duration_minutes}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session End Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_telemedicine_session(session_id):
    """Get telemedicine session details"""
    try:
        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        
        return {
            "success": True,
            "session": {
                "name": session.name,
                "patient": session.patient,
                "patient_display": session.patient_display,
                "practitioner": session.practitioner,
                "practitioner_display": session.practitioner_display,
                "session_type": session.session_type,
                "status": session.status,
                "scheduled_datetime": session.scheduled_datetime,
                "start_datetime": session.start_datetime,
                "end_datetime": session.end_datetime,
                "duration_minutes": session.duration_minutes,
                "room_id": session.room_id,
                "recording_enabled": session.recording_enabled,
                "recording_url": session.recording_url,
                "diagnosis": session.diagnosis,
                "clinical_notes": session.clinical_notes,
                "technical_quality": session.technical_quality,
                "rating": session.rating,
                "encounter": getattr(session, "encounter", None),
                "service_charge": getattr(session, "service_charge", None),
                "medication_request": getattr(session, "medication_request", None),
                "prescriptions": [
                    {
                        "medication": row.medication,
                        "dosage": row.dosage,
                        "frequency": row.frequency,
                        "duration": row.duration,
                        "instructions": row.instructions,
                    }
                    for row in (session.prescriptions or [])
                ],
                "is_practitioner": _is_session_practitioner(session),
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session Get Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def join_telemedicine_session(session_id, user_type=None):
    """Generate secure token and Jitsi config to join session"""
    try:
        from omnexa_healthcare.api.telemedicine_integration import build_join_payload

        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        if session.status not in ["Scheduled", "In Progress"]:
            return {"success": False, "error": "Session is not available"}

        resolved_user_type = user_type or _resolve_join_user_type(session)
        return build_join_payload(session_id, user_type=resolved_user_type)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session Join Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cancel_telemedicine_session(session_id, reason):
    """Cancel a telemedicine session"""
    try:
        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        
        if session.status not in ["Scheduled"]:
            return {"success": False, "error": "Cannot cancel session in current status"}
        
        session.status = "Cancelled"
        session.clinical_notes = f"Cancelled. Reason: {reason}"
        session.save()
        
        # Update queue
        queue_entries = frappe.get_all(
            "Healthcare Telemedicine Queue",
            filters={"session": session_id, "status": "Waiting"},
        )
        
        for entry in queue_entries:
            queue = frappe.get_doc("Healthcare Telemedicine Queue", entry.name)
            queue.status = "Skipped"
            queue.save()
        
        return {"success": True, "status": session.status}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Session Cancel Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_doctor_queue(practitioner_id):
    """Get doctor's patient queue"""
    try:
        queue_entries = frappe.get_all(
            "Healthcare Telemedicine Queue",
            filters={
                "practitioner": practitioner_id,
                "status": ["in", ["Waiting", "In Progress"]],
            },
            fields=["*"],
            order_by="queue_position",
        )
        
        result = []
        for entry in queue_entries:
            session = frappe.get_doc("Healthcare Telemedicine Session", entry.session)
            result.append({
                "queue_id": entry.name,
                "session_id": entry.session,
                "patient": session.patient_display,
                "session_type": session.session_type,
                "queue_position": entry.queue_position,
                "estimated_wait": entry.estimated_wait_minutes,
                "status": entry.status,
                "joined_time": entry.joined_datetime
            })
        
        return {"success": True, "queue": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Queue Get Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def call_next_patient(practitioner_id):
    """Call next patient from queue"""
    try:
        # Get next waiting patient
        queue_entry = frappe.db.get_value("Healthcare Telemedicine Queue", {
            "practitioner": practitioner_id,
            "status": "Waiting"
        }, "name", order_by="queue_position asc")
        
        if not queue_entry:
            return {"success": False, "error": "No patients in queue"}
        
        queue = frappe.get_doc("Healthcare Telemedicine Queue", queue_entry)
        queue.status = "In Progress"
        queue.start_datetime = now()
        queue.save()
        
        # Start session
        session = frappe.get_doc("Healthcare Telemedicine Session", queue.session)
        session.status = "In Progress"
        session.start_datetime = now()
        session.save()
        
        from omnexa_healthcare.api.telemedicine_integration import emit_queue_update, emit_session_event

        emit_session_event(session.name, "patient_called", {
            "session_id": session.name,
            "patient": session.patient_display,
        })
        emit_queue_update(practitioner_id, {"session_id": session.name, "status": "In Progress"})
        
        return {
            "success": True,
            "session_id": session.name,
            "room_id": session.room_id,
            "patient": session.patient_display
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Call Next Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_portal_config():
    """Get telemedicine portal configuration"""
    try:
        from omnexa_healthcare.api.telemedicine_admin import get_config
        config_result = get_config()
        
        if config_result.get("success") and config_result.get("config"):
            config = config_result["config"]
            return {
                "success": True,
                "config": {
                    "enable_video": config.get("enable_video_consultations"),
                    "enable_voice": config.get("enable_voice_consultations"),
                    "enable_chat": config.get("enable_chat_consultations"),
                    "default_duration": config.get("default_session_duration"),
                    "max_duration": config.get("max_session_duration"),
                    "enable_screen_sharing": config.get("enable_screen_sharing"),
                    "enable_whiteboard": config.get("enable_whiteboard"),
                    "enable_file_sharing": config.get("enable_file_sharing"),
                    "video_quality": config.get("video_quality"),
                    "primary_color": "#0066cc",
                    "secondary_color": "#004499"
                }
            }
        else:
            # Return default config if not exists
            return {
                "success": True,
                "config": {
                    "enable_video": True,
                    "enable_voice": True,
                    "enable_chat": True,
                    "default_duration": 30,
                    "max_duration": 60,
                    "enable_screen_sharing": True,
                    "enable_whiteboard": True,
                    "enable_file_sharing": True,
                    "video_quality": "HD",
                    "primary_color": "#0066cc",
                    "secondary_color": "#004499"
                }
            }
    except Exception as e:
        # Return default config on error
        return {
            "success": True,
            "config": {
                "enable_video": True,
                "enable_voice": True,
                "enable_chat": True,
                "default_duration": 30,
                "max_duration": 60,
                "enable_screen_sharing": True,
                "enable_whiteboard": True,
                "enable_file_sharing": True,
                "video_quality": "HD",
                "primary_color": "#0066cc",
                "secondary_color": "#004499"
            }
        }


@frappe.whitelist(allow_guest=True)
def get_available_doctors(specialty=None):
    """Get available doctors for telemedicine"""
    try:
        company = frappe.db.get_value("Company", {"name": "MH"}, "name") or frappe.db.get_value(
            "Company", {}, "name"
        )
        filters = {"status": "Active"}
        if company:
            filters["company"] = company

        doctors = frappe.get_all(
            "Healthcare Practitioner",
            filters=filters,
            fields=["name", "practitioner_name", "website_photo", "company"],
            order_by="practitioner_name asc",
            limit=50,
        )

        resolved_specialty = _resolve_specialty_filter(specialty)
        specialty_fallback = False
        if resolved_specialty:
            filtered = []
            for doctor in doctors:
                assignments = frappe.get_all(
                    "Healthcare Practitioner Branch",
                    filters={"parent": doctor.name, "specialty": resolved_specialty, "is_active": 1},
                    fields=["specialty", "branch"],
                    limit=1,
                )
                if assignments:
                    doctor.specialty = assignments[0].specialty
                    filtered.append(doctor)
            if filtered:
                doctors = filtered
            else:
                specialty_fallback = True

        for doctor in doctors:
            if not getattr(doctor, "specialty", None):
                assignment = frappe.get_all(
                    "Healthcare Practitioner Branch",
                    filters={"parent": doctor.name, "is_active": 1},
                    fields=["specialty"],
                    limit=1,
                )
                doctor.specialty = assignment[0].specialty if assignment else None
            ratings = frappe.get_all(
                "Healthcare Telemedicine Session",
                filters={"practitioner": doctor.name, "rating": [">", 0]},
                fields=["rating"],
                limit=50,
            )
            doctor.average_rating = (
                round(sum(r.rating for r in ratings) / len(ratings), 1) if ratings else 4.8
            )
            doctor.session_count = frappe.db.count(
                "Healthcare Telemedicine Session", {"practitioner": doctor.name, "status": "Completed"}
            )

        return {
            "success": True,
            "doctors": doctors,
            "specialty_resolved": resolved_specialty,
            "specialty_fallback": specialty_fallback,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Get Doctors Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_current_practitioner():
    """Resolve practitioner linked to the logged-in user."""
    try:
        practitioner_id = frappe.db.get_value(
            "Healthcare Practitioner", {"user": frappe.session.user}, "name"
        )
        if not practitioner_id and frappe.session.user != "Guest":
            practitioner_id = frappe.db.get_value(
                "Healthcare Practitioner",
                {"user": ["like", "tele.doctor%"], "status": "Active"},
                "name",
            )
        if not practitioner_id:
            practitioner_id = frappe.db.get_value(
                "Healthcare Practitioner", {"status": "Active", "company": "MH"}, "name"
            ) or frappe.db.get_value(
                "Healthcare Practitioner", {"status": "Active"}, "name"
            )

        if not practitioner_id:
            return {"success": False, "error": "No practitioner found"}

        practitioner = frappe.get_doc("Healthcare Practitioner", practitioner_id)
        return {
            "success": True,
            "practitioner_id": practitioner_id,
            "practitioner_name": practitioner.practitioner_name,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Current Practitioner Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_practitioner_sessions(practitioner_id, status=None, from_date=None, to_date=None):
    """Get practitioner telemedicine sessions for schedule/dashboard views."""
    try:
        filters = {"practitioner": practitioner_id}
        if status:
            filters["status"] = status
        if from_date:
            filters["scheduled_datetime"] = [">=", from_date]
        if to_date:
            if "scheduled_datetime" in filters:
                filters["scheduled_datetime"].append(["<=", f"{to_date} 23:59:59"])
            else:
                filters["scheduled_datetime"] = ["<=", f"{to_date} 23:59:59"]

        sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters=filters,
            fields=[
                "name",
                "patient",
                "patient_display",
                "practitioner",
                "practitioner_display",
                "scheduled_datetime",
                "status",
                "session_type",
                "duration_minutes",
                "rating",
                "clinical_notes",
            ],
            order_by="scheduled_datetime asc",
            limit=100,
        )
        return {"success": True, "sessions": sessions}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Practitioner Sessions Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_available_slots(practitioner_id, date):
    """Return available booking slots for a practitioner on a given date."""
    try:
        from omnexa_healthcare.api.telemedicine_admin import get_config

        config_result = get_config()
        duration = 30
        if config_result.get("success"):
            duration = config_result["config"].get("default_session_duration") or 30

        booked = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                "practitioner": practitioner_id,
                "scheduled_datetime": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
                "status": ["in", ["Scheduled", "In Progress"]],
            },
            fields=["scheduled_datetime", "duration_minutes"],
        )
        booked_times = set()
        for row in booked:
            if row.scheduled_datetime:
                booked_times.add(str(row.scheduled_datetime)[11:16])

        slots = []
        for hour in (9, 10, 11, 14, 15, 16):
            for minute in (0, 30):
                start = f"{hour:02d}:{minute:02d}"
                end_hour = hour + (1 if minute == 30 else 0)
                end_minute = 0 if minute == 30 else 30
                if minute == 30:
                    end_hour = hour + 1
                    end_minute = 0
                end = f"{end_hour:02d}:{end_minute:02d}"
                slots.append(
                    {
                        "start": start,
                        "end": end,
                        "available": start not in booked_times,
                        "duration_minutes": duration,
                    }
                )

        return {"success": True, "slots": slots}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Available Slots Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def book_telemedicine_consultation(data):
    """Book a telemedicine consultation from the patient portal."""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        patient_id = data.get("patient")
        practitioner_id = data.get("practitioner") or data.get("doctor")
        if not patient_id or not practitioner_id:
            return {"success": False, "error": "Patient and practitioner are required"}

        scheduled_datetime = data.get("scheduled_datetime")
        if not scheduled_datetime and data.get("date") and data.get("time"):
            time_value = data["time"]
            if isinstance(time_value, dict):
                time_value = time_value.get("start")
            scheduled_datetime = f"{data['date']} {time_value}"

        company, branch = _resolve_practitioner_context(practitioner_id)
        return create_telemedicine_session(
            {
                "patient": patient_id,
                "practitioner": practitioner_id,
                "session_type": data.get("session_type") or data.get("consultation_type") or "Video",
                "scheduled_datetime": scheduled_datetime,
                "company": company,
                "branch": branch,
                "clinical_notes": data.get("notes"),
                "portal_booking": True,
            }
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Book Telemedicine Consultation Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_patient_sessions(patient_id):
    """Get patient's telemedicine sessions"""
    try:
        sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={"patient": patient_id},
            fields=["*"],
            order_by="scheduled_datetime desc",
            limit=20,
        )
        
        return {"success": True, "sessions": sessions}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine Get Patient Sessions Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_booking_patients(limit=20):
    """Return patients available for portal booking."""
    try:
        company = frappe.db.get_value("Company", {"name": "MH"}, "name") or frappe.db.get_value(
            "Company", {}, "name"
        )
        filters = {"company": company} if company else {}
        patients = frappe.get_all(
            "Healthcare Patient",
            filters=filters,
            fields=["name", "full_name", "company", "branch", "given_name", "family_name"],
            order_by="modified desc",
            limit=int(limit or 20),
        )
        tele_demo = [p for p in patients if (p.full_name or "").startswith("Tele Patient")]
        others = [p for p in patients if p not in tele_demo]
        patients = tele_demo + others
        return {"success": True, "patients": patients[: int(limit or 20)]}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Booking Patients Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_telemedicine_fhir_bundle(session_id):
    """Export FHIR R4 bundle for a telemedicine session."""
    try:
        from omnexa_healthcare.api.telemedicine_integration import build_telemedicine_fhir_bundle

        if not frappe.has_permission("Healthcare Telemedicine Session", "read", session_id):
            frappe.throw("Not permitted")
        return {"success": True, "bundle": build_telemedicine_fhir_bundle(session_id)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Telemedicine FHIR Bundle Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def save_session_prescriptions(session_id, items):
    """Save e-prescription rows on an active telemedicine session."""
    try:
        items = frappe.parse_json(items) if isinstance(items, str) else (items or [])
        session = frappe.get_doc("Healthcare Telemedicine Session", session_id)
        session.set("prescriptions", [])
        for row in items:
            session.append(
                "prescriptions",
                {
                    "medication": row.get("medication"),
                    "dosage": row.get("dosage"),
                    "frequency": row.get("frequency"),
                    "duration": row.get("duration"),
                    "instructions": row.get("instructions"),
                },
            )
        session.save()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Save Session Prescriptions Error")
        return {"success": False, "error": str(e)}


def _resolve_join_user_type(session) -> str:
    practitioner_user = frappe.db.get_value("Healthcare Practitioner", session.practitioner, "user")
    if practitioner_user and frappe.session.user == practitioner_user:
        return "practitioner"
    if frappe.session.user == "Administrator":
        return "practitioner"
    return "participant"


def _is_session_practitioner(session) -> bool:
    return _resolve_join_user_type(session) == "practitioner"


@frappe.whitelist()
def get_patient_clinical_summary(patient_id):
    """Return patient vitals, allergies, medications, and conditions for session UI."""
    try:
        patient = frappe.get_doc("Healthcare Patient", patient_id)
        medications = frappe.get_all(
            "Healthcare Medication Request",
            filters={"patient": patient_id, "status": ["in", ["Draft", "Active", "On Hold"]]},
            fields=["name", "diagnosis", "status", "creation"],
            order_by="creation desc",
            limit=10,
        )
        med_items = []
        for med in medications:
            items = frappe.get_all(
                "Healthcare Medication Request Item",
                filters={"parent": med.name},
                fields=["drug_name", "dose", "frequency"],
                limit=5,
            )
            med_items.extend(items)

        conditions = frappe.get_all(
            "Healthcare Clinical Condition",
            filters={"patient": patient_id},
            fields=["name", "clinical_description", "clinical_status", "icd10_code"],
            order_by="modified desc",
            limit=10,
        )

        from omnexa_healthcare.api.telemedicine_monitoring import get_patient_readings

        readings = get_patient_readings(patient_id).get("readings") or []

        return {
            "success": True,
            "summary": {
                "patient_id": patient_id,
                "full_name": patient.full_name,
                "allergies": patient.allergies_free_text or "",
                "medications": med_items,
                "conditions": conditions,
                "readings": readings[:10],
            },
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Clinical Summary Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_telemedicine_patient(data):
    """Create a patient from the telemedicine doctor portal."""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else (data or {})
        full_name = (data.get("full_name") or data.get("name") or "").strip()
        if not full_name:
            return {"success": False, "error": "Patient name is required"}

        parts = full_name.split(None, 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else parts[0]

        company = data.get("company")
        branch = data.get("branch")
        
        # Try to resolve from practitioner if provided
        practitioner_id = data.get("practitioner")
        if practitioner_id and (not company or not branch):
            try:
                company, branch = _resolve_practitioner_context(practitioner_id)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Resolve Practitioner Context Error")
        
        # Fallback to default company and branch
        if not company or not branch:
            company = frappe.db.get_value("Company", {}, "name")
            if company and not branch:
                branch = frappe.db.get_value("Branch", {"company": company}, "name")
        
        # Final check
        if not company:
            return {"success": False, "error": "No Company found in system. Please configure a Company first."}
        if not branch:
            return {"success": False, "error": f"No Branch found for Company '{company}'. Please configure a Branch first."}

        phone = (data.get("phone") or "").strip() or f"+2010{frappe.generate_hash(length=8)}"
        telecom = [{"contact_system": "phone", "contact_use": "mobile", "value": phone, "rank": 1}]
        if data.get("email"):
            telecom.append(
                {"contact_system": "email", "contact_use": "home", "value": data.get("email"), "rank": 2}
            )

        patient_data = {
            "doctype": "Healthcare Patient",
            "naming_series": "HP-.#####",
            "company": company,
            "branch": branch,
            "given_name": given_name,
            "family_name": family_name,
            "gender": data.get("gender"),
            "birth_date": data.get("birth_date") or data.get("dob"),
            "active": 1,
            "registration_status": "Complete",
            "address_line1": data.get("address"),
            "city": data.get("city"),
            "district": data.get("area"),
            "allergies_free_text": data.get("allergies"),
            "identifiers": [
                {
                    "identifier_use": "official",
                    "identifier_type": "MRN",
                    "value": f"TEL-{frappe.generate_hash(length=8)}",
                    "is_primary_mrn": 1,
                }
            ],
            "telecom": telecom,
        }

        doc = frappe.get_doc(patient_data).insert(ignore_permissions=True)

        return {"success": True, "patient_id": doc.name, "full_name": doc.full_name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Telemedicine Patient Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def start_doctor_consultation(patient, practitioner=None, session_type="Video"):
    """Start an immediate telemedicine session from the doctor portal."""
    try:
        if not patient:
            return {"success": False, "error": "Patient is required"}

        if not practitioner:
            ctx = get_current_practitioner()
            if not ctx.get("success"):
                return ctx
            practitioner = ctx.get("practitioner_id")

        session_type = _normalize_session_type(session_type)
        company, branch = _resolve_practitioner_context(practitioner)
        return create_telemedicine_session(
            {
                "patient": patient,
                "practitioner": practitioner,
                "session_type": session_type,
                "company": company,
                "branch": branch,
                "portal_booking": True,
            }
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Start Doctor Consultation Error")
        return {"success": False, "error": str(e)}


def get_next_queue_position(practitioner_id):
    """Get next queue position for a practitioner"""
    last_position = frappe.db.get_value("Healthcare Telemedicine Queue", {
        "practitioner": practitioner_id,
        "status": ["in", ["Waiting", "In Progress"]]
    }, "queue_position", order_by="queue_position desc")
    
    return (last_position or 0) + 1


def on_session_create(doc, method):
    """Hook called when telemedicine session is created"""
    from omnexa_healthcare.api.telemedicine_integration import emit_queue_update

    emit_queue_update(doc.practitioner, {"session_id": doc.name, "status": doc.status})


def on_session_update(doc, method):
    """Hook called when telemedicine session is updated"""
    if doc.status == "Completed" and not getattr(doc, "encounter", None):
        from omnexa_healthcare.api.telemedicine_integration import finalize_completed_session

        finalize_completed_session(doc)
