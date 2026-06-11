# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Remote patient monitoring readings and alerts."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


def _rpm_enabled() -> bool:
	return bool(frappe.db.get_single_value("Healthcare Settings", "enable_remote_monitoring"))


def _alert_level(metric_type: str, value: float) -> str:
	thresholds = {
		"Heart Rate": (50, 120),
		"SpO2": (90, 100),
		"Blood Pressure": (60, 180),
		"Glucose": (70, 250),
	}
	lo, hi = thresholds.get(metric_type, (0, 9999))
	if value < lo or value > hi:
		return "Critical" if (value < lo * 0.8 or value > hi * 1.2) else "Warning"
	return "Normal"


@frappe.whitelist()
def record_rpm_reading(patient: str, metric_type: str, value: float, company: str, unit: str | None = None, device_id: str | None = None) -> dict:
	if not _rpm_enabled():
		frappe.throw(_("Remote monitoring is disabled."), title=_("RPM"))
	alert = _alert_level(metric_type, float(value))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Remote Monitoring Reading",
			"patient": patient,
			"device_id": device_id,
			"metric_type": metric_type,
			"value": value,
			"unit": unit,
			"reading_datetime": now_datetime(),
			"alert_level": alert,
			"company": company,
		}
	)
	doc.insert(ignore_permissions=True)
	if alert in ("Warning", "Critical"):
		try:
			from omnexa_healthcare.api.patient_notifications import queue_patient_notification

			queue_patient_notification(patient, f"RPM alert: {metric_type} = {value} ({alert})", channel="Push")
		except Exception:
			pass
	return {"ok": True, "reading": doc.name, "alert_level": alert}


@frappe.whitelist()
def get_rpm_dashboard(patient: str, limit: int = 20) -> dict:
	readings = frappe.get_all(
		"Healthcare Remote Monitoring Reading",
		filters={"patient": patient},
		fields=["name", "metric_type", "value", "unit", "reading_datetime", "alert_level"],
		order_by="reading_datetime desc",
		limit_page_length=limit,
	)
	by_metric: dict[str, list] = {}
	for row in readings:
		by_metric.setdefault(row.metric_type, []).append(row)
	return {"patient": patient, "readings": readings, "by_metric": by_metric, "alert_count": sum(1 for r in readings if r.alert_level != "Normal")}
