# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from omnexa_healthcare.bed_units import care_unit_for_bed, is_critical_care_bed, is_neonatal_bed


def compute_alert_level(doc) -> str:
	"""Derive monitoring alert from vitals (ICU / NICU thresholds)."""
	critical = False
	warning = False
	care_unit = (doc.care_unit or "").strip()

	hr = flt(doc.heart_rate)
	rr = flt(doc.respiratory_rate)
	spo2 = flt(doc.spo2)
	sys_bp = flt(doc.bp_systolic)
	temp = flt(doc.temperature_c)

	if care_unit in ("NICU", "Nursery"):
		if spo2 and spo2 < 85:
			critical = True
		elif spo2 and spo2 < 90:
			warning = True
		if hr and (hr > 180 or hr < 80):
			critical = True
		elif hr and (hr > 160 or hr < 100):
			warning = True
		if rr and (rr > 70 or rr < 20):
			critical = True
		elif rr and (rr > 60 or rr < 30):
			warning = True
		if temp and (temp > 38.0 or temp < 36.0):
			warning = True
	else:
		if spo2 and spo2 < 88:
			critical = True
		elif spo2 and spo2 < 92:
			warning = True
		if hr and (hr > 150 or hr < 40):
			critical = True
		elif hr and (hr > 120 or hr < 50):
			warning = True
		if rr and rr > 40:
			critical = True
		elif rr and rr > 28:
			warning = True
		if sys_bp and sys_bp > 180:
			critical = True
		elif sys_bp and sys_bp > 160:
			warning = True
		if temp and temp > 39.5:
			critical = True
		elif temp and temp > 38.5:
			warning = True

	if critical:
		return "Critical"
	if warning:
		return "Warning"
	return "Normal"


class HealthcareCriticalCareMonitoring(Document):
	def validate(self):
		self._validate_admission_bed()
		if not self.recorded_by:
			self.recorded_by = frappe.session.user
		if not self.care_unit:
			bed_type = frappe.db.get_value("Healthcare Bed", self.bed, "bed_type")
			cu = care_unit_for_bed(bed_type)
			self.care_unit = "NICU" if cu == "NICU" or is_neonatal_bed(bed_type) else "ICU"
		self.alert_level = compute_alert_level(self)

	def _validate_admission_bed(self):
		admit = frappe.db.get_value(
			"Healthcare Admission",
			self.admission,
			["patient", "bed", "status", "company", "branch"],
			as_dict=True,
		)
		if not admit:
			frappe.throw(_("Admission does not exist."), title=_("Admission"))
		if admit.patient != self.patient:
			frappe.throw(_("Patient must match admission."), title=_("Patient"))
		if admit.status != "admitted":
			frappe.throw(_("Patient must be actively admitted."), title=_("Admission"))
		if self.bed and admit.bed != self.bed:
			frappe.throw(_("Bed must match the active admission bed."), title=_("Bed"))
		bed_type = frappe.db.get_value("Healthcare Bed", self.bed, "bed_type")
		if not is_critical_care_bed(bed_type) and bed_type != "Pediatric":
			frappe.throw(_("Monitoring is only for ICU, HDU, NICU, or Nursery beds."), title=_("Bed"))
		if admit.company != self.company or admit.branch != self.branch:
			frappe.throw(_("Admission must belong to the same company and branch."), title=_("Branch"))
