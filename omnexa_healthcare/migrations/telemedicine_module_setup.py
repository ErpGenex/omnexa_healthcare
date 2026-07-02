# -*- coding: utf-8 -*-
import frappe
from frappe.custom.doctype.customize_form import CustomizeForm


def execute():
    """Migration to setup Telemedicine Module"""
    
    # Create default Telemedicine Configuration
    create_default_configuration()
    
    # Add telemedicine to Appointment Type options
    update_appointment_types()
    
    # Add telemedicine links to Patient and Practitioner
    add_telemedicine_links()


def create_default_configuration():
    """Create default telemedicine configuration"""
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
            "jitsi_domain": "",
            "turn_server_url": "",
            "stun_server_url": "stun:stun.l.google.com:19302",
            "session_timeout_minutes": 15
        })
        config.insert()
        frappe.db.commit()


def update_appointment_types():
    """Add Telehealth to appointment type options if not exists"""
    appointment_type_doctype = frappe.get_meta("Healthcare Appointment")
    
    # Check if Telehealth option exists in session_type field
    session_type_field = appointment_type_doctype.get_field("appointment_type")
    if session_type_field:
        options = session_type_field.options or ""
        if "Telehealth" not in options:
            new_options = options + "\nTelehealth" if options else "Telehealth"
            
            customize_form = frappe.new_doc("Customize Form")
            customize_form.dt = "Healthcare Appointment"
            customize_form.fields = [{
                "fieldname": "appointment_type",
                "options": new_options
            }]
            customize_form.save()
            frappe.db.commit()


def add_telemedicine_links():
    """Add telemedicine links to Patient and Practitioner DocTypes"""
    
    # Add telemedicine sessions link to Patient
    patient_meta = frappe.get_meta("Healthcare Patient")
    patient_links = patient_meta.get("links") or []
    
    telemedicine_session_link = {
        "link_doctype": "Healthcare Telemedicine Session",
        "link_fieldname": "patient",
        "hidden": 0
    }
    
    if not any(link.get("link_doctype") == "Healthcare Telemedicine Session" for link in patient_links):
        customize_form = frappe.new_doc("Customize Form")
        customize_form.dt = "Healthcare Patient"
        customize_form.links = patient_links + [telemedicine_session_link]
        customize_form.save()
        frappe.db.commit()
    
    # Add telemedicine sessions link to Practitioner
    practitioner_meta = frappe.get_meta("Healthcare Practitioner")
    practitioner_links = practitioner_meta.get("links") or []
    
    telemedicine_session_link_practitioner = {
        "link_doctype": "Healthcare Telemedicine Session",
        "link_fieldname": "practitioner",
        "hidden": 0
    }
    
    if not any(link.get("link_doctype") == "Healthcare Telemedicine Session" for link in practitioner_links):
        customize_form = frappe.new_doc("Customize Form")
        customize_form.dt = "Healthcare Practitioner"
        customize_form.links = practitioner_links + [telemedicine_session_link_practitioner]
        customize_form.save()
        frappe.db.commit()
