# -*- coding: utf-8 -*-
import frappe
from frappe import _
from datetime import datetime, timedelta


CANONICAL_TELEMEDICINE_CONFIG = "Healthcare Telemedicine Configuration"

TELEMEDICINE_ADMIN_ROLES = (
	"System Manager",
	"Company Admin",
	"Physician",
	"Healthcare Administrator",
	"Desk User",
)


def _require_telemedicine_admin():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to access telemedicine admin."), frappe.PermissionError)
	roles = set(frappe.get_roles())
	if not roles.intersection(TELEMEDICINE_ADMIN_ROLES):
		frappe.throw(_("Not permitted to access telemedicine admin."), frappe.PermissionError)


def _default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_value("Company", {"name": "MH"}, "name")
		or frappe.db.get_value("Company", {}, "name")
	)


def _specialty_code_for_department(department_name):
	if not department_name:
		return None
	code = frappe.db.get_value("Healthcare Department", department_name, "department_code") or ""
	code = code.upper()
	mapping = {
		"TELE-GEN": "GEN",
		"TELE-DERM": "DER",
		"TELE-CARD": "CAR",
		"TELE-PED": "PED",
		"DERM": "DER",
		"CARD": "CAR",
		"PED": "PED",
		"GEN": "GEN",
	}
	if code in mapping:
		return mapping[code]
	if code.startswith("TELE-"):
		return mapping.get(code, code.replace("TELE-", ""))
	return code or None


def _practitioner_rows(company=None, status=None, department=None, limit=100):
	filters = {}
	if company:
		filters["company"] = company
	if status:
		filters["status"] = status

	limit = int(limit or 100)
	tele_rows = frappe.get_all(
		"Healthcare Practitioner",
		filters={**filters, "user": ["like", "tele.doctor%"]},
		fields=["name", "practitioner_name", "status", "company"],
		order_by="practitioner_name asc",
		ignore_permissions=True,
	)
	remaining = max(limit - len(tele_rows), 0)
	other_filters = dict(filters)
	if tele_rows:
		other_filters["name"] = ["not in", [row.name for row in tele_rows]]
	other_rows = frappe.get_all(
		"Healthcare Practitioner",
		filters=other_filters,
		fields=["name", "practitioner_name", "status", "company"],
		order_by="practitioner_name asc",
		limit=remaining or limit,
		ignore_permissions=True,
	)
	rows = tele_rows + other_rows

	specialty_code = _specialty_code_for_department(department)
	enriched = []
	for row in rows:
		assignment = frappe.get_all(
			"Healthcare Practitioner Branch",
			filters={"parent": row.name, "is_active": 1},
			fields=["specialty", "branch"],
			limit=1,
			ignore_permissions=True,
		)
		specialty_name = None
		specialty_id = assignment[0].specialty if assignment else None
		if specialty_id:
			specialty_name = frappe.db.get_value("Healthcare Specialty", specialty_id, "specialty_name")
		row.specialty = specialty_name or specialty_id
		row.department = specialty_name or "-"

		if specialty_code:
			specialty_doc_code = frappe.db.get_value("Healthcare Specialty", specialty_id, "specialty_code") if specialty_id else None
			if specialty_doc_code != specialty_code and specialty_id != specialty_code:
				continue

		enriched.append(row)

	return enriched[:limit]


@frappe.whitelist()
def get_admin_departments(company=None):
	"""List healthcare departments for telemedicine admin filters."""
	try:
		_require_telemedicine_admin()
		company = company or _default_company()
		filters = {"status": "Active"}
		if company:
			filters["company"] = company

		departments = frappe.get_all(
			"Healthcare Department",
			filters=filters,
			fields=["name", "department_name", "department_code", "branch"],
			order_by="department_name asc",
			limit=200,
			ignore_permissions=True,
		)
		tele_departments = [
			d
			for d in departments
			if (d.department_code or "").startswith("TELE")
			or "telemedicine" in (d.department_name or "").lower()
			or "عن بعد" in (d.department_name or "")
		]
		departments = tele_departments or departments[:20]
		return {"success": True, "departments": departments}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Admin Departments Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_admin_doctors(department=None, status=None, company=None, limit=100):
	"""List practitioners for telemedicine admin."""
	try:
		_require_telemedicine_admin()
		company = company or _default_company()
		doctors = _practitioner_rows(
			company=company,
			status=status or None,
			department=department or None,
			limit=limit,
		)
		return {"success": True, "doctors": doctors}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Admin Doctors Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_admin_practitioners(company=None, limit=500):
	"""Practitioner picklist for admin forms."""
	try:
		_require_telemedicine_admin()
		company = company or _default_company()
		practitioners = _practitioner_rows(company=company, limit=limit)
		return {"success": True, "practitioners": practitioners}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Admin Practitioners Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_admin_patients(company=None, limit=100):
	"""Patient list for telemedicine admin."""
	try:
		_require_telemedicine_admin()
		company = company or _default_company()
		filters = {}
		if company:
			filters["company"] = company

		patients = frappe.get_all(
			"Healthcare Patient",
			filters=filters,
			fields=["name", "full_name", "active", "company", "branch"],
			order_by="modified desc",
			limit=int(limit or 100),
			ignore_permissions=True,
		)

		for patient in patients:
			phone = frappe.db.get_value(
				"Healthcare Patient Telecom",
				{
					"parent": patient.name,
					"parenttype": "Healthcare Patient",
					"contact_system": "phone",
				},
				"value",
			)
			patient.mobile_no = phone

		tele_first = [p for p in patients if (p.full_name or "").startswith("Tele Patient")]
		others = [p for p in patients if p not in tele_first]
		patients = tele_first + others
		return {"success": True, "patients": patients[: int(limit or 100)]}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Admin Patients Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_admin_sessions(status=None, practitioner=None, date=None, limit=100):
	"""List telemedicine sessions for admin portal."""
	try:
		_require_telemedicine_admin()
		filters = {}
		if status:
			filters["status"] = status
		if practitioner:
			filters["practitioner"] = practitioner
		if date:
			filters["scheduled_datetime"] = ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]

		sessions = frappe.get_all(
			"Healthcare Telemedicine Session",
			filters=filters,
			fields=[
				"name",
				"patient",
				"practitioner",
				"scheduled_datetime",
				"status",
				"session_type",
				"room_id",
			],
			order_by="scheduled_datetime desc",
			limit=int(limit or 100),
			ignore_permissions=True,
		)
		for session in sessions:
			session.patient_name = frappe.db.get_value("Healthcare Patient", session.patient, "full_name")
			session.practitioner_name = frappe.db.get_value(
				"Healthcare Practitioner", session.practitioner, "practitioner_name"
			)
		return {"success": True, "sessions": sessions}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Admin Sessions Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_admin_session(data):
	"""Create telemedicine session from admin portal."""
	try:
		_require_telemedicine_admin()
		from omnexa_healthcare.api.telemedicine import create_telemedicine_session, _resolve_practitioner_context

		data = frappe.parse_json(data) if isinstance(data, str) else (data or {})
		patient_id = data.get("patient")
		practitioner_id = data.get("practitioner")
		if not patient_id or not practitioner_id:
			return {"success": False, "error": "Patient and practitioner are required"}

		type_map = {"video": "Video", "voice": "Voice", "chat": "Chat"}
		session_type = data.get("session_type") or type_map.get(
			str(data.get("consultation_type") or "").lower(), "Video"
		)

		scheduled_datetime = data.get("scheduled_datetime")
		if not scheduled_datetime and data.get("date") and data.get("time"):
			time_value = data["time"]
			if len(str(time_value)) == 5:
				time_value = f"{time_value}:00"
			scheduled_datetime = f"{data['date']} {time_value}"

		company, branch = _resolve_practitioner_context(practitioner_id)
		return create_telemedicine_session(
			{
				"patient": patient_id,
				"practitioner": practitioner_id,
				"session_type": session_type,
				"scheduled_datetime": scheduled_datetime,
				"company": company,
				"branch": branch,
				"clinical_notes": data.get("notes") or data.get("clinical_notes"),
				"portal_booking": True,
			}
		)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Admin Session Error")
		return {"success": False, "error": str(e)}


def cleanup_duplicate_telemedicine_configurations():
	"""Remove orphan telemedicine config rows created when issingle was false."""
	if not frappe.db.table_exists("Healthcare Telemedicine Configuration"):
		return
	for name in frappe.get_all("Healthcare Telemedicine Configuration", pluck="name"):
		if name != CANONICAL_TELEMEDICINE_CONFIG:
			try:
				frappe.delete_doc(
					"Healthcare Telemedicine Configuration",
					name,
					force=1,
					ignore_permissions=True,
				)
			except Exception:
				frappe.db.delete("Healthcare Telemedicine Configuration", {"name": name})


def ensure_telemedicine_configuration():
	"""Return the singleton telemedicine configuration, creating defaults when missing."""
	cleanup_duplicate_telemedicine_configurations()

	try:
		return frappe.get_single(CANONICAL_TELEMEDICINE_CONFIG)
	except frappe.DoesNotExistError:
		pass

	singles = frappe.db.get_singles_dict(CANONICAL_TELEMEDICINE_CONFIG)
	if singles:
		doc = frappe.new_doc(CANONICAL_TELEMEDICINE_CONFIG)
		doc.update(singles)
		return doc

	config = frappe.get_doc(
		{
			"doctype": CANONICAL_TELEMEDICINE_CONFIG,
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
	)
	config.save(ignore_permissions=True)
	return config


@frappe.whitelist()
def get_config():
    """Get telemedicine configuration"""
    try:
        config = ensure_telemedicine_configuration()
        
        return {
            "success": True,
            "config": {
                "enable_video_consultations": config.enable_video_consultations,
                "enable_voice_consultations": config.enable_voice_consultations,
                "enable_chat_consultations": config.enable_chat_consultations,
                "default_session_duration": config.default_session_duration,
                "max_session_duration": config.max_session_duration,
                "enable_waitlist": config.enable_waitlist,
                "max_concurrent_sessions": config.max_concurrent_sessions,
                "allow_recording": config.allow_recording,
                "auto_record": config.auto_record,
                "recording_retention_days": config.recording_retention_days,
                "enable_screen_sharing": config.enable_screen_sharing,
                "enable_whiteboard": config.enable_whiteboard,
                "enable_file_sharing": config.enable_file_sharing,
                "max_file_size_mb": config.max_file_size_mb,
                "allowed_file_types": config.allowed_file_types,
                "video_quality": config.video_quality,
                "enable_ai_transcription": config.enable_ai_transcription,
                "enable_ai_summarization": config.enable_ai_summarization,
                "jitsi_domain": config.jitsi_domain or "meet.jit.si",
                "turn_server_url": config.turn_server_url,
                "stun_server_url": config.stun_server_url,
                "session_timeout_minutes": config.session_timeout_minutes
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Config Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_config(data):
    """Update telemedicine configuration"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        # Ensure config exists
        config_result = get_config()
        if not config_result.get("success"):
            return {"success": False, "error": "Configuration not found"}
        
        config = ensure_telemedicine_configuration()
        
        # Update fields
        for field in [
            "enable_video_consultations", "enable_voice_consultations", "enable_chat_consultations",
            "default_session_duration", "max_session_duration", "enable_waitlist", "max_concurrent_sessions",
            "allow_recording", "auto_record", "recording_retention_days", "enable_screen_sharing",
            "enable_whiteboard", "enable_file_sharing", "max_file_size_mb", "allowed_file_types",
            "video_quality", "enable_ai_transcription", "enable_ai_summarization",
            "jitsi_domain", "jitsi_app_id", "jitsi_secret", "turn_server_url", "turn_username",
            "turn_credential", "stun_server_url", "session_timeout_minutes"
        ]:
            if field in data:
                setattr(config, field, data[field])
        
        config.save()
        
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Config Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_active_sessions():
    """Get currently active telemedicine sessions"""
    try:
        sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={"status": "In Progress"},
            fields=["*"],
            order_by="start_datetime desc",
        )
        
        return {"success": True, "sessions": sessions}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Active Sessions Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_session_stats(filters=None):
    """Get telemedicine session statistics"""
    try:
        filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
        
        base_filters = {}
        if filters.get("from_date"):
            base_filters["scheduled_datetime"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            if "scheduled_datetime" in base_filters:
                base_filters["scheduled_datetime"].append(["<=", filters.get("to_date")])
            else:
                base_filters["scheduled_datetime"] = ["<=", filters.get("to_date")]
        if filters.get("practitioner"):
            base_filters["practitioner"] = filters.get("practitioner")
        if filters.get("company"):
            base_filters["company"] = filters.get("company")
        
        # Get counts by status
        stats = {}
        for status in ["Scheduled", "In Progress", "Completed", "Cancelled", "No Show"]:
            status_filters = base_filters.copy()
            status_filters["status"] = status
            count = frappe.db.count("Healthcare Telemedicine Session", status_filters)
            stats[status.lower().replace(" ", "_")] = count
        
        # Get total sessions today
        today = frappe.utils.nowdate()
        today_count = frappe.db.count("Healthcare Telemedicine Session", {
            "scheduled_datetime": ["like", f"{today}%"]
        })
        stats["today_sessions"] = today_count
        
        # Get average rating
        completed_sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                **base_filters,
                "status": "Completed",
                "rating": [">", 0],
            },
            fields=["rating"],
        )
        
        if completed_sessions:
            avg_rating = sum(s.rating for s in completed_sessions) / len(completed_sessions)
            stats["average_rating"] = round(avg_rating, 1)
        else:
            stats["average_rating"] = 0.0
        
        # Get total duration
        completed_with_duration = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                **base_filters,
                "status": "Completed",
                "duration_minutes": [">", 0],
            },
            fields=["duration_minutes"],
        )

        total_duration = sum(s.duration_minutes or 0 for s in completed_with_duration)
        stats["total_duration_minutes"] = total_duration
        stats["average_duration_minutes"] = round(total_duration / len(completed_with_duration), 1) if completed_with_duration else 0
        stats["total_sessions"] = sum(
            stats.get(key, 0)
            for key in ("scheduled", "in_progress", "completed", "cancelled", "no_show")
        )

        return {"success": True, "stats": stats}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Session Stats Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_system_health():
    """Get system health status"""
    try:
        health = {}
        
        # Check video server (simulated - in production, actual health check)
        config_result = get_config()
        if config_result.get("success") and config_result.get("config"):
            config = config_result["config"]
            health["video_server"] = "connected" if config.get("jitsi_domain") else "not_configured"
            health["turn_server"] = "connected" if config.get("turn_server_url") else "not_configured"
            health["stun_server"] = "connected" if config.get("stun_server_url") else "not_configured"
        else:
            health["video_server"] = "not_configured"
            health["turn_server"] = "not_configured"
            health["stun_server"] = "not_configured"
        
        # Check database
        try:
            frappe.db.sql("SELECT 1")
            health["database"] = "connected"
        except:
            health["database"] = "error"
        
        # Check Redis (if configured)
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            health["redis"] = "connected"
        except:
            health["redis"] = "not_configured"
        
        # Check storage
        health["storage"] = "ok"
        
        # Get active sessions count
        active_count = frappe.db.count("Healthcare Telemedicine Session", {"status": "In Progress"})
        health["active_sessions"] = active_count
        
        return {"success": True, "health": health}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get System Health Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_alerts():
    """Get system alerts"""
    try:
        alerts = []
        
        # Check for abnormal readings
        abnormal_readings = frappe.get_all(
            "Healthcare Remote Monitoring Reading",
            filters={"alert_level": "Critical"},
            fields=["*"],
            order_by="reading_datetime desc",
            limit=10,
        )
        
        for reading in abnormal_readings:
            alerts.append({
                "type": "critical",
                "text": f"Abnormal reading: {reading.metric_type} = {reading.value} {reading.unit}",
                "time": reading.reading_datetime,
                "source": "monitoring"
            })
        
        # Check for failed sessions
        failed_sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={"status": "Cancelled", "technical_quality": "Poor"},
            fields=["*"],
            order_by="end_datetime desc",
            limit=10,
        )
        
        for session in failed_sessions:
            alerts.append({
                "type": "warning",
                "text": f"Session failed: {session.connection_issues or 'Unknown issue'}",
                "time": session.end_datetime,
                "source": "session"
            })
        
        # Check for high queue wait times
        long_wait_queues = frappe.get_all(
            "Healthcare Telemedicine Queue",
            filters={"status": "Waiting", "estimated_wait_minutes": [">", 30]},
            fields=["*"],
        )
        
        for queue in long_wait_queues:
            alerts.append({
                "type": "warning",
                "text": f"Long wait time: {queue.estimated_wait_minutes} minutes",
                "time": queue.joined_datetime,
                "source": "queue"
            })
        
        return {"success": True, "alerts": alerts}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Alerts Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_practitioner_stats(practitioner_id):
    """Get practitioner-specific statistics"""
    try:
        # Get session counts
        total_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            "practitioner": practitioner_id
        })
        
        completed_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            "practitioner": practitioner_id,
            "status": "Completed"
        })
        
        # Get average rating
        rated_sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                "practitioner": practitioner_id,
                "status": "Completed",
                "rating": [">", 0],
            },
            fields=["rating"],
        )
        
        avg_rating = 0
        if rated_sessions:
            avg_rating = round(sum(s.rating for s in rated_sessions) / len(rated_sessions), 1)
        
        # Get today's sessions
        today = frappe.utils.nowdate()
        today_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            "practitioner": practitioner_id,
            "scheduled_datetime": ["like", f"{today}%"]
        })
        
        # Get current queue
        queue_count = frappe.db.count("Healthcare Telemedicine Queue", {
            "practitioner": practitioner_id,
            "status": "Waiting"
        })
        
        return {
            "success": True,
            "stats": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "average_rating": avg_rating,
                "today_sessions": today_sessions,
                "queue_count": queue_count
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Practitioner Stats Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_patient_stats(patient_id):
    """Get patient-specific statistics"""
    try:
        # Get session counts
        total_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            "patient": patient_id
        })
        
        completed_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            "patient": patient_id,
            "status": "Completed"
        })
        
        # Get device count
        device_count = frappe.db.count("Healthcare Remote Monitoring Device", {
            "patient": patient_id,
            "status": "Active"
        })
        
        # Get recent readings count
        recent_readings = frappe.db.count("Healthcare Remote Monitoring Reading", {
            "patient": patient_id,
            "reading_datetime": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
        })
        
        return {
            "success": True,
            "stats": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "active_devices": device_count,
                "recent_readings": recent_readings
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Patient Stats Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_revenue_report(filters=None):
    """Get telemedicine revenue report"""
    try:
        filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
        
        base_filters = {"status": "Completed"}
        if filters.get("from_date"):
            base_filters["scheduled_datetime"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            if "scheduled_datetime" in base_filters:
                base_filters["scheduled_datetime"].append(["<=", filters.get("to_date")])
            else:
                base_filters["scheduled_datetime"] = ["<=", filters.get("to_date")]
        if filters.get("company"):
            base_filters["company"] = filters.get("company")
        
        # Get sessions with linked appointments (for revenue)
        sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters=base_filters,
            fields=["name", "appointment", "practitioner", "scheduled_datetime"],
        )
        
        total_revenue = 0
        session_revenue = []
        
        for session in sessions:
            if session.appointment:
                appointment = frappe.get_doc("Healthcare Appointment", session.appointment)
                revenue = appointment.booking_fee or 0
                total_revenue += revenue
                session_revenue.append({
                    "session": session.name,
                    "practitioner": session.practitioner,
                    "date": session.scheduled_datetime,
                    "revenue": revenue
                })
        
        return {
            "success": True,
            "report": {
                "total_revenue": total_revenue,
                "total_sessions": len(sessions),
                "average_revenue_per_session": round(total_revenue / len(sessions), 2) if sessions else 0,
                "details": session_revenue
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Revenue Report Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_usage_report(filters=None):
    """Get telemedicine usage analytics report"""
    try:
        filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
        
        base_filters = {}
        if filters.get("from_date"):
            base_filters["scheduled_datetime"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            if "scheduled_datetime" in base_filters:
                base_filters["scheduled_datetime"].append(["<=", filters.get("to_date")])
            else:
                base_filters["scheduled_datetime"] = ["<=", filters.get("to_date")]
        
        # Get sessions by type
        video_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "session_type": "Video"
        })
        voice_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "session_type": "Voice"
        })
        chat_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "session_type": "Chat"
        })
        
        # Get sessions by status
        scheduled_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "status": "Scheduled"
        })
        completed_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "status": "Completed"
        })
        cancelled_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "status": "Cancelled"
        })
        no_show_count = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "status": "No Show"
        })
        
        # Get average session duration
        completed_sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                **base_filters,
                "status": "Completed",
                "duration_minutes": [">", 0],
            },
            fields=["duration_minutes"],
        )
        
        avg_duration = 0
        if completed_sessions:
            avg_duration = round(sum(s.duration_minutes or 0 for s in completed_sessions) / len(completed_sessions), 1)
        
        return {
            "success": True,
            "report": {
                "by_type": {
                    "video": video_count,
                    "voice": voice_count,
                    "chat": chat_count
                },
                "by_status": {
                    "scheduled": scheduled_count,
                    "completed": completed_count,
                    "cancelled": cancelled_count,
                    "no_show": no_show_count
                },
                "average_duration_minutes": avg_duration,
                "completion_rate": round(completed_count / (completed_count + cancelled_count + no_show_count) * 100, 1) if (completed_count + cancelled_count + no_show_count) > 0 else 0
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Usage Report Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_practitioner_performance_report(practitioner_id, filters=None):
    """Get practitioner-specific performance report"""
    try:
        filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
        
        base_filters = {"practitioner": practitioner_id}
        if filters.get("from_date"):
            base_filters["scheduled_datetime"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            if "scheduled_datetime" in base_filters:
                base_filters["scheduled_datetime"].append(["<=", filters.get("to_date")])
            else:
                base_filters["scheduled_datetime"] = ["<=", filters.get("to_date")]
        
        # Get session counts
        total_sessions = frappe.db.count("Healthcare Telemedicine Session", base_filters)
        completed_sessions = frappe.db.count("Healthcare Telemedicine Session", {
            **base_filters,
            "status": "Completed"
        })
        
        # Get average rating
        rated_sessions = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                **base_filters,
                "status": "Completed",
                "rating": [">", 0],
            },
            fields=["rating"],
        )
        
        avg_rating = 0
        if rated_sessions:
            avg_rating = round(sum(s.rating for s in rated_sessions) / len(rated_sessions), 1)
        
        # Get average duration
        completed_with_duration = frappe.get_all(
            "Healthcare Telemedicine Session",
            filters={
                **base_filters,
                "status": "Completed",
                "duration_minutes": [">", 0],
            },
            fields=["duration_minutes"],
        )
        
        avg_duration = 0
        if completed_with_duration:
            avg_duration = round(sum(s.duration_minutes or 0 for s in completed_with_duration) / len(completed_with_duration), 1)
        
        return {
            "success": True,
            "report": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "completion_rate": round(completed_sessions / total_sessions * 100, 1) if total_sessions > 0 else 0,
                "average_rating": avg_rating,
                "average_duration_minutes": avg_duration
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Practitioner Performance Report Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_dashboard_stats(filters=None):
    """Aggregate stats for the telemedicine admin dashboard."""
    try:
        stats_result = get_session_stats(filters)
        if not stats_result.get("success"):
            return stats_result

        stats = stats_result["stats"]
        active_sessions = frappe.db.count(
            "Healthcare Telemedicine Session", {"status": "In Progress"}
        )
        active_doctors = frappe.db.count(
            "Healthcare Practitioner", {"status": "Active"}
        )
        alerts_result = get_alerts()
        alerts = alerts_result.get("alerts", []) if alerts_result.get("success") else []

        revenue_result = get_revenue_report(filters)
        total_revenue = 0
        if revenue_result.get("success"):
            total_revenue = revenue_result.get("report", {}).get("total_revenue", 0)

        return {
            "success": True,
            "stats": {
                "active_sessions": active_sessions,
                "today_sessions": stats.get("today_sessions", 0),
                "satisfaction": stats.get("average_rating", 0),
                "revenue": total_revenue,
                "issues": len(alerts),
                "active_doctors": active_doctors,
                "total_sessions": stats.get("total_sessions", 0),
                "completed_sessions": stats.get("completed", 0),
            },
            "alerts": alerts,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Dashboard Stats Error")
        return {"success": False, "error": str(e)}
