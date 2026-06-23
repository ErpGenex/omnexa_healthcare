#!/usr/bin/env python3
"""Bootstrap missing healthcare Journey portal pages."""
from __future__ import annotations

import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "omnexa_healthcare", "page")

PORTALS = [
	("healthcare_morgue_desk", "healthcare-morgue-desk", "Morgue Desk", "get_morgue_dashboard", "cases", "nurse"),
	("healthcare_ot_board", "healthcare-ot-board", "OT Board", "get_ot_board", "cases", "nurse"),
	("healthcare_dialysis_desk", "healthcare-dialysis-desk", "Dialysis Desk", "get_dialysis_dashboard", "sessions", "nurse"),
	("healthcare_ld_board", "healthcare-ld-board", "L&D Board", "get_ld_board_dashboard", "cases", "nurse"),
	("healthcare_optometry_desk", "healthcare-optometry-desk", "Optometry Desk", "get_optometry_dashboard", "orders", "physician"),
	("healthcare_blood_desk", "healthcare-blood-desk", "Blood Bank", "get_blood_bank_dashboard", "units", "nurse"),
	("healthcare_rehab_desk", "healthcare-rehab-desk", "Physiotherapy", "get_rehab_orders", "orders", "nurse"),
	("healthcare_diet_desk", "healthcare-diet-desk", "Nutrition Desk", "get_nutrition_orders", "orders", "nurse"),
	("healthcare_appointments_desk", "healthcare-appointments-desk", "Appointments", "get_appointments_directory", "appointments", "reception"),
	("healthcare_patients_desk", "healthcare-patients-desk", "Patients", "get_patients_directory", "patients", "reception"),
]

JS_TEMPLATE = '''frappe.pages["{page}"].on_page_load = function (wrapper) {{
	omnexa_healthcare.portal.mount(wrapper, {{
		deskTitle: __("{title}"),
		titleAr: "{title_ar}",
		titleEn: "{title}",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "{sidebar}",
		api: "omnexa_healthcare.api.specialty_desks.{api}",
		rowsField: "{rows}",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: {columns},
		links: {links},
		homeRoute: "/app/healthcare-workcenter",
	}});
}};
'''

TITLE_AR = {
	"Morgue Desk": "المشرحة",
	"OT Board": "غرف العمليات",
	"Dialysis Desk": "غسيل الكلى",
	"L&D Board": "الولادة",
	"Optometry Desk": "البصريات",
	"Blood Bank": "بنك الدم",
	"Physiotherapy": "علاج طبيعي",
	"Nutrition Desk": "التغذية",
	"Appointments": "المواعيد",
	"Patients": "دليل المرضى",
}

COLUMNS = {
	"default": [
		{"field": "name", "ar": "المرجع", "en": "Ref"},
		{"field": "patient", "ar": "المريض", "en": "Patient"},
		{"field": "status", "ar": "الحالة", "en": "Status"},
	],
	"appointments": [
		{"field": "name", "ar": "الموعد", "en": "Appointment"},
		{"field": "patient_display", "ar": "المريض", "en": "Patient"},
		{"field": "practitioner", "ar": "الطبيب", "en": "Doctor"},
		{"field": "appointment_date", "ar": "التاريخ", "en": "Date"},
		{"field": "status", "ar": "الحالة", "en": "Status"},
	],
	"patients": [
		{"field": "name", "ar": "MRN", "en": "MRN"},
		{"field": "full_name", "ar": "الاسم", "en": "Name"},
		{"field": "mobile", "ar": "الجوال", "en": "Mobile"},
		{"field": "gender", "ar": "النوع", "en": "Gender"},
	],
	"units": [
		{"field": "unit_number", "ar": "الوحدة", "en": "Unit"},
		{"field": "blood_group", "ar": "الفصيلة", "en": "Group"},
		{"field": "component", "ar": "المكون", "en": "Component"},
		{"field": "expiry_date", "ar": "الانتهاء", "en": "Expiry"},
	],
}

LINKS = {
	"appointments": [
		{"labelAr": "موعد جديد", "labelEn": "New Appointment", "route": "/app/healthcare-appointment/new-healthcare-appointment-1", "icon": "➕"},
		{"labelAr": "التقويم", "labelEn": "Calendar", "route": "/app/healthcare-appointment-calendar", "icon": "🗓"},
	],
	"patients": [
		{"labelAr": "مريض جديد", "labelEn": "New Patient", "route": "/app/healthcare-patient/new-healthcare-patient-1", "icon": "➕"},
		{"labelAr": "الاستقبال", "labelEn": "Reception", "route": "/app/healthcare-reception-desk", "icon": "🏥"},
	],
}


def main():
	for folder, page, title, api, rows, sidebar in PORTALS:
		path = os.path.join(BASE, folder)
		os.makedirs(path, exist_ok=True)
		js_path = os.path.join(path, f"{folder}.js")
		json_path = os.path.join(path, f"{folder}.json")
		col_key = rows if rows in COLUMNS else "default"
		link_key = rows if rows in LINKS else None
		columns = json.dumps(COLUMNS[col_key], ensure_ascii=False)
		links = json.dumps(LINKS.get(link_key, []), ensure_ascii=False)
		if not os.path.exists(js_path):
			open(js_path, "w", encoding="utf-8").write(
				JS_TEMPLATE.format(
					page=page,
					title=title,
					title_ar=TITLE_AR.get(title, title),
					api=api,
					rows=rows,
					sidebar=sidebar,
					columns=columns,
					links=links,
				)
			)
		if not os.path.exists(json_path):
			open(json_path, "w", encoding="utf-8").write(
				json.dumps(
					{
						"doctype": "Page",
						"module": "Omnexa Healthcare",
						"name": page,
						"page_name": page,
						"standard": "Yes",
						"title": title,
						"roles": [{"role": "System Manager"}, {"role": "Desk User"}],
					},
					indent=1,
				)
			)
		print("ok", page)


if __name__ == "__main__":
	main()
