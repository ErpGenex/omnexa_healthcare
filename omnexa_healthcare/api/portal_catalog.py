# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare Journey portals catalog — single source of truth."""

from __future__ import annotations

import frappe
from frappe.utils import cint

PORTAL_CATALOG: list[dict] = [
	{"id": "demo-hub", "route": "/app/healthcare-demo-hub", "page": "healthcare-demo-hub", "icon": "🎯", "category": "admin", "roles": ["System Manager"], "label_ar": "مركز الديمو", "label_en": "Demo Hub"},
	{"id": "device-admin", "route": "/app/healthcare-device-admin", "page": "healthcare-device-admin", "icon": "🔌", "category": "admin", "roles": ["System Manager", "Company Admin"], "label_ar": "ربط الأجهزة الطبية", "label_en": "Medical Devices"},
	{"id": "reception", "route": "/app/healthcare-reception-desk", "page": "healthcare-reception-desk", "icon": "🏥", "category": "core", "roles": ["Healthcare Receptionist"], "label_ar": "الاستقبال", "label_en": "Reception"},
	{"id": "cashier", "route": "/app/healthcare-cashier-desk", "page": "healthcare-cashier-desk", "icon": "💰", "category": "core", "roles": ["Healthcare Cashier"], "label_ar": "الخزينة", "label_en": "Cashier"},
	{"id": "physician", "route": "/app/healthcare-physician-workbench", "page": "healthcare-physician-workbench", "icon": "👨‍⚕️", "category": "core", "roles": ["Healthcare Physician"], "label_ar": "الطبيب", "label_en": "Physician"},
	{"id": "patient", "route": "/app/healthcare-patient-consumer", "page": "healthcare-patient-consumer", "icon": "👤", "category": "core", "roles": ["Healthcare Patient Portal"], "label_ar": "بوابة المريض", "label_en": "Patient Portal"},
	{"id": "queue", "route": "/app/healthcare-patient-queue", "page": "healthcare-patient-queue", "icon": "📋", "category": "core", "roles": ["Healthcare Receptionist", "Healthcare Nurse", "Healthcare Physician"], "label_ar": "الطابور", "label_en": "Queue"},
	{"id": "appointment", "route": "/app/healthcare-appointments-desk", "page": "healthcare-appointments-desk", "icon": "📅", "category": "core", "roles": ["Healthcare Receptionist"], "label_ar": "المواعيد", "label_en": "Appointments"},
	{"id": "patients", "route": "/app/healthcare-patients-desk", "page": "healthcare-patients-desk", "icon": "👥", "category": "core", "roles": ["Healthcare Receptionist"], "label_ar": "دليل المرضى", "label_en": "Patients"},
	{"id": "nursing", "route": "/app/healthcare-nursing-portal", "page": "healthcare-nursing-portal", "icon": "🩹", "category": "clinical", "roles": ["Healthcare Nurse"], "label_ar": "التمريض", "label_en": "Nursing"},
	{"id": "pharmacy", "route": "/app/healthcare-pharmacy-desk", "page": "healthcare-pharmacy-desk", "icon": "💊", "category": "clinical", "roles": ["Healthcare Pharmacist"], "label_ar": "الصيدلية", "label_en": "Pharmacy"},
	{"id": "rx-verify", "route": "/app/healthcare-pharmacy-rx-verify", "page": "healthcare-pharmacy-rx-verify", "icon": "✅", "category": "clinical", "roles": ["Healthcare Pharmacist"], "label_ar": "تحقق الروشتة", "label_en": "Rx Verify"},
	{"id": "lab", "route": "/app/healthcare-lab-workbench", "page": "healthcare-lab-workbench", "icon": "🧪", "category": "clinical", "roles": ["Healthcare Physician", "Healthcare Nurse"], "label_ar": "المختبر", "label_en": "Lab"},
	{"id": "radiology", "route": "/app/healthcare-radiology-worklist", "page": "healthcare-radiology-worklist", "icon": "🩻", "category": "clinical", "roles": ["Healthcare Physician", "Healthcare Nurse"], "label_ar": "الأشعة", "label_en": "Radiology"},
	{"id": "dicom", "route": "/app/healthcare-dicom-viewer", "page": "healthcare-dicom-viewer", "icon": "🖼️", "category": "clinical", "roles": ["Healthcare Physician"], "label_ar": "DICOM", "label_en": "DICOM Viewer"},
	{"id": "chart", "route": "/app/healthcare-patient-chart", "page": "healthcare-patient-chart", "icon": "📁", "category": "clinical", "roles": ["Healthcare Physician"], "label_ar": "الملف الطبي", "label_en": "Chart"},
	{"id": "erx", "route": "/app/healthcare-erx-writer", "page": "healthcare-erx-writer", "icon": "📝", "category": "clinical", "roles": ["Healthcare Physician"], "label_ar": "الروشتة", "label_en": "eRx"},
	{"id": "er", "route": "/app/healthcare-er-board", "page": "healthcare-er-board", "icon": "🚨", "category": "departments", "roles": ["Healthcare Physician", "Healthcare Nurse"], "label_ar": "الطوارئ", "label_en": "ER"},
	{"id": "icu", "route": "/app/healthcare-icu-board", "page": "healthcare-icu-board", "icon": "🏥", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "ICU", "label_en": "ICU"},
	{"id": "beds", "route": "/app/healthcare-bed-map", "page": "healthcare-bed-map", "icon": "🛏️", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "الأسرة", "label_en": "Beds"},
	{"id": "ot", "route": "/app/healthcare-ot-board", "page": "healthcare-ot-board", "icon": "🔪", "category": "departments", "roles": ["Healthcare Physician"], "label_ar": "العمليات", "label_en": "OT"},
	{"id": "dialysis", "route": "/app/healthcare-dialysis-desk", "page": "healthcare-dialysis-desk", "icon": "💧", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "غسيل الكلى", "label_en": "Dialysis"},
	{"id": "ld", "route": "/app/healthcare-ld-board", "page": "healthcare-ld-board", "icon": "👶", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "الولادة", "label_en": "L&D"},
	{"id": "optometry", "route": "/app/healthcare-optometry-desk", "page": "healthcare-optometry-desk", "icon": "👓", "category": "departments", "roles": ["Healthcare Physician"], "label_ar": "البصريات", "label_en": "Optometry"},
	{"id": "dental", "route": "/app/healthcare-dental-chart", "page": "healthcare-dental-chart", "icon": "🦷", "category": "departments", "roles": ["Healthcare Physician"], "label_ar": "الأسنان", "label_en": "Dental"},
	{"id": "rehab", "route": "/app/healthcare-rehab-desk", "page": "healthcare-rehab-desk", "icon": "🦴", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "علاج طبيعي", "label_en": "Physio"},
	{"id": "diet", "route": "/app/healthcare-diet-desk", "page": "healthcare-diet-desk", "icon": "🥗", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "التغذية", "label_en": "Nutrition"},
	{"id": "blood", "route": "/app/healthcare-blood-desk", "page": "healthcare-blood-desk", "icon": "🩸", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "بنك الدم", "label_en": "Blood Bank"},
	{"id": "morgue", "route": "/app/healthcare-morgue-desk", "page": "healthcare-morgue-desk", "icon": "⚰️", "category": "departments", "roles": ["Healthcare Nurse"], "label_ar": "المشرحة", "label_en": "Morgue"},
	{"id": "finance", "route": "/app/healthcare-finance-desk", "page": "healthcare-finance-desk", "icon": "💼", "category": "management", "roles": ["Healthcare CFO"], "label_ar": "المالية", "label_en": "Finance"},
	{"id": "executive", "route": "/app/healthcare-executive-dashboard", "page": "healthcare-executive-dashboard", "icon": "📊", "category": "management", "roles": ["Healthcare Executive"], "label_ar": "التنفيذي", "label_en": "Executive"},
	{"id": "telehealth", "route": "/app/healthcare-telehealth-room", "page": "healthcare-telehealth-room", "icon": "📹", "category": "digital", "roles": ["Healthcare Physician"], "label_ar": "Telehealth", "label_en": "Telehealth"},
	{"id": "calendar", "route": "/app/healthcare-appointment-calendar", "page": "healthcare-appointment-calendar", "icon": "🗓", "category": "support", "roles": ["Healthcare Receptionist"], "label_ar": "التقويم", "label_en": "Calendar"},
	{"id": "roster", "route": "/app/healthcare-practitioner-roster", "page": "healthcare-practitioner-roster", "icon": "📆", "category": "support", "roles": ["Healthcare Executive"], "label_ar": "جدول الأطباء", "label_en": "Roster"},
]

CATEGORY_LABELS = {
	"admin": {"ar": "الإدارة والتكامل", "en": "Admin & Integration"},
	"core": {"ar": "النواة", "en": "Core"},
	"clinical": {"ar": "سريري", "en": "Clinical"},
	"departments": {"ar": "أقسام وتخصصات", "en": "Departments"},
	"management": {"ar": "إدارة", "en": "Management"},
	"digital": {"ar": "رقمي", "en": "Digital"},
	"support": {"ar": "مساندة", "en": "Support"},
}


def _page_exists(page_name: str) -> bool:
	return bool(frappe.db.exists("Page", page_name))


@frappe.whitelist()
def get_portal_catalog(include_missing: int = 0) -> list[dict]:
	out = []
	for row in PORTAL_CATALOG:
		item = dict(row)
		item["exists"] = _page_exists(item["page"])
		if item["exists"] or cint(include_missing):
			out.append(item)
	return out


@frappe.whitelist()
def get_grouped_portal_catalog(include_missing: int = 0) -> list[dict]:
	from frappe.utils import cint

	groups: dict[str, list] = {}
	for row in get_portal_catalog(include_missing=cint(include_missing)):
		groups.setdefault(row["category"], []).append(row)
	result = []
	for cat, portals in groups.items():
		labels = CATEGORY_LABELS.get(cat, {"ar": cat, "en": cat})
		result.append({"category": cat, "label_ar": labels["ar"], "label_en": labels["en"], "portals": portals})
	return result
