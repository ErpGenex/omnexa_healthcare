# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ADT — transfers, census, ER admit bridge."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def transfer_bed(admission: str, to_bed: str, reason: str | None = None) -> dict:
	admit = frappe.get_doc("Healthcare Admission", admission)
	from_bed = admit.bed
	if from_bed == to_bed:
		frappe.throw(_("Patient is already on this bed."))
	transfer = frappe.get_doc(
		{
			"doctype": "Healthcare Adt Transfer",
			"admission": admission,
			"patient": admit.patient,
			"from_bed": from_bed,
			"to_bed": to_bed,
			"transfer_datetime": now_datetime(),
			"reason": reason,
			"company": admit.company,
			"branch": admit.branch,
		}
	).insert()
	if from_bed:
		frappe.db.set_value("Healthcare Bed", from_bed, "status", "Available", update_modified=False)
	frappe.db.set_value("Healthcare Bed", to_bed, "status", "Occupied", update_modified=False)
	admit.db_set("bed", to_bed, update_modified=False)
	return {"transfer": transfer.name, "bed": to_bed}


@frappe.whitelist()
def api_get_ipd_census(branch: str) -> list[dict]:
	if not branch:
		frappe.throw(_("branch is required"))
	return frappe.db.sql(
		"""
		SELECT a.name AS admission, a.patient, a.bed, a.admission_datetime, a.status, b.bed_type
		FROM `tabHealthcare Admission` a
		LEFT JOIN `tabHealthcare Bed` b ON b.name = a.bed
		WHERE a.branch = %s AND a.status IN ('Admitted', 'In Progress')
		ORDER BY a.admission_datetime DESC
		""",
		branch,
		as_dict=True,
	)


def create_admission_from_er(er_visit: str) -> str:
	er = frappe.get_doc("Healthcare Er Visit", er_visit)
	if er.admission:
		return er.admission
	bed = frappe.db.get_value(
		"Healthcare Bed",
		{"branch": er.branch, "status": "Available"},
		"name",
	)
	admit = frappe.get_doc(
		{
			"doctype": "Healthcare Admission",
			"naming_series": "ADM-.#####",
			"patient": er.patient,
			"company": er.company,
			"branch": er.branch,
			"admission_datetime": now_datetime(),
			"admission_type": "emergency",
			"status": "Admitted",
			"bed": bed,
		}
	).insert(ignore_permissions=True)
	if bed:
		frappe.db.set_value("Healthcare Bed", bed, "status", "Occupied", update_modified=False)
	return admit.name
