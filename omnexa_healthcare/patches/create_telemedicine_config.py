import frappe

def execute():
    """Create default Telemedicine Configuration"""
    if not frappe.db.exists("Healthcare Telemedicine Configuration", "Healthcare Telemedicine Configuration"):
        config = frappe.get_doc({
            "doctype": "Healthcare Telemedicine Configuration",
            "name": "Healthcare Telemedicine Configuration",
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
            "session_timeout_minutes": 15
        })
        config.insert()
        frappe.db.commit()
        print("Telemedicine Configuration created successfully")
    else:
        print("Telemedicine Configuration already exists")
