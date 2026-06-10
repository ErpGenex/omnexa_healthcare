# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ICU / NICU monitoring board and vitals recording."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from omnexa_healthcare.bed_units import CRITICAL_CARE_BED_TYPES
from omnexa_healthcare.omnexa_healthcare.doctype.healthcare_critical_care_monitoring.healthcare_critical_care_monitoring import (
	compute_alert_level,
)


@frappe.whitelist()
def record_monitoring(payload: str | dict) -> dict:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	required = ("patient", "admission", "bed", "company", "branch")
	for key in required:
		if not data.get(key):
			frappe.throw(_("{0} is required").format(key))
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Critical Care Monitoring",
			"patient": data.patient,
			"admission": data.admission,
			"bed": data.bed,
			"care_unit": data.get("care_unit"),
			"recorded_at": data.get("recorded_at") or now_datetime(),
			"heart_rate": data.get("heart_rate"),
			"respiratory_rate": data.get("respiratory_rate"),
			"spo2": data.get("spo2"),
			"bp_systolic": data.get("bp_systolic"),
			"bp_diastolic": data.get("bp_diastolic"),
			"temperature_c": data.get("temperature_c"),
			"fio2_percent": data.get("fio2_percent"),
			"ventilator_mode": data.get("ventilator_mode"),
			"weight_g": data.get("weight_g"),
			"gestational_age_weeks": data.get("gestational_age_weeks"),
			"notes": data.get("notes"),
			"company": data.company,
			"branch": data.branch,
		}
	).insert()
	return {"name": doc.name, "alert_level": doc.alert_level}


@frappe.whitelist()
def api_get_critical_care_board(branch: str, care_unit: str | None = None) -> list[dict]:
	if not branch:
		frappe.throw(_("branch is required"))
	if care_unit in ("NICU", "Nursery"):
		bed_types = ("NICU", "Nursery")
	elif care_unit == "ICU":
		bed_types = ("ICU", "HDU")
	else:
		bed_types = tuple(CRITICAL_CARE_BED_TYPES)
	placeholders = ", ".join(["%s"] * len(bed_types))
	args: list = [branch, *bed_types]

	rows = frappe.db.sql(
		f"""
		SELECT
			a.name AS admission,
			a.patient,
			a.patient_display,
			a.admission_datetime,
			b.name AS bed,
			b.bed_label,
			b.bed_type,
			u.unit_name,
			u.unit_type,
			m.name AS last_monitoring,
			m.recorded_at AS last_recorded_at,
			m.heart_rate,
			m.respiratory_rate,
			m.spo2,
			m.bp_systolic,
			m.bp_diastolic,
			m.temperature_c,
			m.fio2_percent,
			m.weight_g,
			m.gestational_age_weeks,
			m.alert_level,
			m.care_unit
		FROM `tabHealthcare Admission` a
		INNER JOIN `tabHealthcare Bed` b ON b.name = a.bed
		LEFT JOIN `tabHealthcare Service Unit` u ON u.name = b.service_unit
		LEFT JOIN `tabHealthcare Critical Care Monitoring` m ON m.name = (
			SELECT m2.name
			FROM `tabHealthcare Critical Care Monitoring` m2
			WHERE m2.admission = a.name
			ORDER BY m2.recorded_at DESC
			LIMIT 1
		)
		WHERE a.branch = %s
		  AND a.status = 'admitted'
		  AND b.bed_type IN ({placeholders})
		ORDER BY
			FIELD(IFNULL(m.alert_level, 'Normal'), 'Critical', 'Warning', 'Normal'),
			a.admission_datetime DESC
		LIMIT 200
		""",
		tuple(args),
		as_dict=True,
	)
	for row in rows:
		row["minutes_since_vitals"] = _minutes_since(row.get("last_recorded_at"))
		if not row.get("care_unit"):
			from omnexa_healthcare.bed_units import care_unit_for_bed, is_neonatal_bed

			row["care_unit"] = "NICU" if is_neonatal_bed(row.bed_type) else "ICU"
	return rows


def _minutes_since(dt) -> int | None:
	if not dt:
		return None
	from frappe.utils import time_diff_in_seconds

	return int(time_diff_in_seconds(now_datetime(), dt) / 60)


@frappe.whitelist()
def preview_alert_level(payload: str | dict) -> str:
	data = frappe.parse_json(payload) if isinstance(payload, str) else payload
	stub = frappe._dict(
		care_unit=data.get("care_unit") or "ICU",
		heart_rate=flt(data.get("heart_rate")),
		respiratory_rate=flt(data.get("respiratory_rate")),
		spo2=flt(data.get("spo2")),
		bp_systolic=flt(data.get("bp_systolic")),
		temperature_c=flt(data.get("temperature_c")),
	)
	return compute_alert_level(stub)
