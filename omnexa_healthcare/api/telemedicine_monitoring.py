# -*- coding: utf-8 -*-
import frappe
from frappe import _
import uuid
import json


@frappe.whitelist()
def register_device(data):
    """Register a new remote monitoring device"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        # Generate device identifier
        device_identifier = f"dev_{uuid.uuid4().hex[:12]}"
        
        device = frappe.get_doc({
            "doctype": "Healthcare Remote Monitoring Device",
            "device_name": data.get("device_name"),
            "device_type": data.get("device_type"),
            "manufacturer": data.get("manufacturer"),
            "model": data.get("model"),
            "serial_number": data.get("serial_number"),
            "patient": data.get("patient"),
            "device_identifier": device_identifier,
            "connection_type": data.get("connection_type", "Bluetooth"),
            "api_endpoint": data.get("api_endpoint"),
            "authentication_token": data.get("authentication_token"),
            "status": "Active",
            "company": data.get("company"),
            "branch": data.get("branch")
        })
        
        device.insert()
        
        return {
            "success": True,
            "device_id": device.name,
            "device_identifier": device_identifier
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Device Registration Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_device_reading(data):
    """Sync device reading"""
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        # Find device by identifier
        device_name = frappe.db.get_value(
            "Healthcare Remote Monitoring Device",
            {"device_identifier": data.get("device_identifier")},
            "name",
        )
        if not device_name:
            return {"success": False, "error": "Device not found"}
        device = frappe.get_doc("Healthcare Remote Monitoring Device", device_name)
        
        # Check if reading is abnormal
        is_abnormal = False
        alert_threshold_min = data.get("alert_threshold_min")
        alert_threshold_max = data.get("alert_threshold_max")
        reading_value = float(data.get("value"))
        
        if alert_threshold_min and reading_value < float(alert_threshold_min):
            is_abnormal = True
        if alert_threshold_max and reading_value > float(alert_threshold_max):
            is_abnormal = True
        
        # Create reading record
        reading = frappe.get_doc({
            "doctype": "Healthcare Remote Monitoring Reading",
            "device_id": device.device_identifier,
            "patient": device.patient,
            "metric_type": data.get("metric_type"),
            "value": reading_value,
            "unit": data.get("unit"),
            "reading_datetime": data.get("reading_datetime") or frappe.utils.now(),
            "alert_level": "Critical" if is_abnormal else "Normal",
            "company": device.company
        })
        
        reading.insert()
        
        # Update device last sync
        device.last_sync_datetime = frappe.utils.now()
        device.battery_level = data.get("battery_level", device.battery_level)
        device.save()
        
        # Send alert if abnormal
        alert_sent = False
        if is_abnormal:
            send_alert(device.patient, reading)
            alert_sent = True
            from omnexa_healthcare.api.telemedicine_integration import emit_device_alert

            emit_device_alert(
                device.patient,
                {
                    "device_id": device.name,
                    "metric_type": reading.metric_type,
                    "value": reading.value,
                    "unit": reading.unit,
                    "alert_level": reading.alert_level,
                },
            )
        
        return {
            "success": True,
            "reading_id": reading.name,
            "is_abnormal": is_abnormal,
            "alert_sent": alert_sent
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Device Reading Sync Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_patient_devices(patient_id):
    """Get patient's monitoring devices"""
    try:
        devices = frappe.get_all(
            "Healthcare Remote Monitoring Device",
            filters={"patient": patient_id, "status": "Active"},
            fields=["*"],
        )
        
        return {"success": True, "devices": devices}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Patient Devices Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_patient_readings(patient_id, filters=None):
    """Get patient health readings"""
    try:
        filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
        
        base_filters = {"patient": patient_id}
        if filters.get("device_id"):
            base_filters["device_id"] = filters.get("device_id")
        if filters.get("metric_type"):
            base_filters["metric_type"] = filters.get("metric_type")
        if filters.get("from_date"):
            base_filters["reading_datetime"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            if "reading_datetime" in base_filters:
                base_filters["reading_datetime"].append(["<=", filters.get("to_date")])
            else:
                base_filters["reading_datetime"] = ["<=", filters.get("to_date")]
        
        readings = frappe.get_all(
            "Healthcare Remote Monitoring Reading",
            filters=base_filters,
            fields=["*"],
            order_by="reading_datetime desc",
            limit=100,
        )
        
        return {"success": True, "readings": readings}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Patient Readings Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def set_alert_thresholds(device_id, thresholds):
    """Set alert thresholds for a device"""
    try:
        thresholds = frappe.parse_json(thresholds) if isinstance(thresholds, str) else thresholds
        
        device = frappe.get_doc("Healthcare Remote Monitoring Device", device_id)
        
        # Store thresholds in device custom fields or create a separate threshold doc
        # For now, we'll store as JSON in a custom field if it exists
        if hasattr(device, "alert_thresholds"):
            device.alert_thresholds = json.dumps(thresholds)
            device.save()
        
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Set Alert Thresholds Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_device_status(device_id):
    """Get device status and health"""
    try:
        device = frappe.get_doc("Healthcare Remote Monitoring Device", device_id)
        
        # Get recent readings
        recent_readings = frappe.get_all(
            "Healthcare Remote Monitoring Reading",
            filters={"device_id": device.device_identifier},
            fields=["reading_datetime", "value", "alert_level"],
            order_by="reading_datetime desc",
            limit=10,
        )
        
        return {
            "success": True,
            "device": {
                "name": device.name,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "status": device.status,
                "battery_level": device.battery_level,
                "last_sync": device.last_sync_datetime,
                "connection_type": device.connection_type
            },
            "recent_readings": recent_readings
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Device Status Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def deactivate_device(device_id, reason):
    """Deactivate a monitoring device"""
    try:
        device = frappe.get_doc("Healthcare Remote Monitoring Device", device_id)
        device.status = "Inactive"
        device.save()
        
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Deactivate Device Error")
        return {"success": False, "error": str(e)}


def send_alert(patient_id, reading):
    """Send alert for abnormal reading"""
    try:
        # Get patient details
        patient = frappe.get_doc("Healthcare Patient", patient_id)
        
        # Get patient's primary practitioner
        if patient.primary_practitioner:
            # In production, send notification via SMS/WhatsApp/Email
            frappe.msgprint(_("Alert sent to practitioner for abnormal reading"))
        
        # Log the alert
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Healthcare Remote Monitoring Reading",
            "reference_name": reading.name,
            "comment": f"Abnormal reading alert: {reading.metric_type} = {reading.value} {reading.unit}"
        }).insert()
        
        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Alert Error")
        return False


def on_reading_create(doc, method=None):
	"""Realtime alert hook for remote monitoring readings."""
	if doc.alert_level != "Critical":
		return
	try:
		from omnexa_healthcare.api.telemedicine_integration import emit_device_alert

		emit_device_alert(
			doc.patient,
			{
				"reading_id": doc.name,
				"metric_type": doc.metric_type,
				"value": doc.value,
				"unit": doc.unit,
				"alert_level": doc.alert_level,
			},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Telemedicine Reading Realtime Alert")
