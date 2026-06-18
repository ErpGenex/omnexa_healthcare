# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Integrated Dental clinic desk — interactive chart + curriculum + ERP."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from omnexa_healthcare.api.dental import FDI_ADULT, get_patient_dental_chart, upsert_dental_chart_entry
from omnexa_healthcare.api.erp_desk_helpers import (
	default_department_warehouse,
	get_accounts_summary,
	get_purchases_summary,
	get_stock_rows,
	item_code,
	resolve_company_branch,
	warehouse_qty,
)

# Academic year → tooth-specific lessons (clinical ERP linkage)
DENTAL_CURRICULUM: dict[int, dict[str, list[dict]]] = {
	1: {
		"11": [{"id": "Y1-T11-1", "title_ar": "تشريح السن الأمامي", "title_en": "Anterior Tooth Anatomy", "item_code": "DEMO-HC-SYRINGE"}],
		"16": [{"id": "Y1-T16-1", "title_ar": "مورفولوجيا الرحى", "title_en": "Molar Morphology", "item_code": "DEMO-HC-GAUZE"}],
		"26": [{"id": "Y1-T26-1", "title_ar": "الإطباق", "title_en": "Occlusion Basics", "item_code": "DEMO-HC-GLOVES"}],
		"36": [{"id": "Y1-T36-1", "title_ar": "الفك السفلي", "title_en": "Mandible Anatomy", "item_code": "DEMO-HC-SYRINGE"}],
	},
	2: {
		"14": [{"id": "Y2-T14-1", "title_ar": "حشوات تجميلية", "title_en": "Composite Fillings", "item_code": "DEMO-HC-GAUZE"}],
		"24": [{"id": "Y2-T24-1", "title_ar": "حشوات تجميلية", "title_en": "Composite Fillings", "item_code": "DEMO-HC-GAUZE"}],
		"36": [{"id": "Y2-T36-1", "title_ar": "علاج العصب مقدمة", "title_en": "Intro Endodontics", "item_code": "DEMO-HC-AMOX500"}],
	},
	3: {
		"16": [{"id": "Y3-T16-1", "title_ar": "تاج مؤقت", "title_en": "Temporary Crown", "item_code": "DEMO-HC-GAUZE"}],
		"46": [{"id": "Y3-T46-1", "title_ar": "خلع جراحي", "title_en": "Surgical Extraction", "item_code": "DEMO-HC-GLOVES"}],
	},
	4: {
		"11": [{"id": "Y4-T11-1", "title_ar": "تقويم مقدمة", "title_en": "Orthodontics Intro", "item_code": "DEMO-HC-GAUZE"}],
		"31": [{"id": "Y4-T31-1", "title_ar": "زراعة أسنان", "title_en": "Implant Planning", "item_code": "DEMO-HC-SYRINGE"}],
	},
	5: {
		"21": [{"id": "Y5-T21-1", "title_ar": "تجميل الابتسامة", "title_en": "Smile Design", "item_code": "DEMO-HC-GAUZE"}],
		"41": [{"id": "Y5-T41-1", "title_ar": "تجميل الابتسامة", "title_en": "Smile Design", "item_code": "DEMO-HC-GAUZE"}],
	},
}

# Year-level curriculum (interactive chart sidebar — matches dental academy layout)
YEAR_LESSONS: dict[int, list[dict]] = {
	1: [
		{"id": "Y1-L1", "title_ar": "تشريح الأسنان العام", "title_en": "General Dental Anatomy", "teeth": ["11", "21", "31", "41"]},
		{"id": "Y1-L2", "title_ar": "أنواع الأسنان ووظائفها", "title_en": "Types of Teeth and Functions", "teeth": ["13", "23", "33", "43", "16", "26"]},
		{"id": "Y1-L3", "title_ar": "أسطح الأسنان والمعالم", "title_en": "Tooth Surfaces and Landmarks", "teeth": ["16", "26", "36", "46"]},
		{"id": "Y1-L4", "title_ar": "الترقيم الدولي", "title_en": "International Numbering", "teeth": [str(t) for t in FDI_ADULT]},
		{"id": "Y1-L5", "title_ar": "المصطلحات الاتجاهية", "title_en": "Directional Terms", "teeth": ["14", "24", "34", "44"]},
		{"id": "Y1-L6", "title_ar": "تكوين الأسنان", "title_en": "Tooth Development", "teeth": ["12", "22", "32", "42"]},
	],
	2: [
		{"id": "Y2-L1", "title_ar": "حشوات تجميلية", "title_en": "Composite Fillings", "teeth": ["14", "24"]},
		{"id": "Y2-L2", "title_ar": "علاج العصب — مقدمة", "title_en": "Intro Endodontics", "teeth": ["36", "46"]},
		{"id": "Y2-L3", "title_ar": "أمراض اللثة", "title_en": "Periodontal Disease", "teeth": ["17", "27", "37", "47"]},
	],
	3: [
		{"id": "Y3-L1", "title_ar": "تاج مؤقت", "title_en": "Temporary Crown", "teeth": ["16", "26"]},
		{"id": "Y3-L2", "title_ar": "خلع جراحي", "title_en": "Surgical Extraction", "teeth": ["46", "36"]},
		{"id": "Y3-L3", "title_ar": "تعويضات جزئية", "title_en": "Partial Dentures", "teeth": ["15", "25", "35", "45"]},
	],
	4: [
		{"id": "Y4-L1", "title_ar": "تقويم — مقدمة", "title_en": "Orthodontics Intro", "teeth": ["11", "21"]},
		{"id": "Y4-L2", "title_ar": "زراعة أسنان", "title_en": "Implant Planning", "teeth": ["31", "41"]},
		{"id": "Y4-L3", "title_ar": "جراحة الفك", "title_en": "Oral Surgery", "teeth": ["18", "28", "38", "48"]},
	],
	5: [
		{"id": "Y5-L1", "title_ar": "تجميل الابتسامة", "title_en": "Smile Design", "teeth": ["21", "41"]},
		{"id": "Y5-L2", "title_ar": "تبييض الأسنان", "title_en": "Teeth Whitening", "teeth": ["11", "12", "21", "22"]},
		{"id": "Y5-L3", "title_ar": "إدارة العيادة", "title_en": "Clinic Management", "teeth": []},
	],
}

_FDI_POSITION_AR = {
	1: "قاطع", 2: "قاطع جانبي", 3: "ناب", 4: "ضاحك أول", 5: "ضاحك ثاني", 6: "رحى أولى", 7: "رحى ثانية", 8: "رحى ثالثة",
}
_FDI_POSITION_EN = {
	1: "Central Incisor", 2: "Lateral Incisor", 3: "Canine", 4: "First Premolar", 5: "Second Premolar",
	6: "First Molar", 7: "Second Molar", 8: "Third Molar",
}
_FDI_QUADRANT_AR = {1: "علوي أيمن", 2: "علوي أيسر", 3: "سفلي أيسر", 4: "سفلي أيمن"}
_FDI_QUADRANT_EN = {1: "Upper Right", 2: "Upper Left", 3: "Lower Left", 4: "Lower Right"}


def _build_tooth_labels() -> dict[str, dict]:
	labels: dict[str, dict] = {}
	for tooth in FDI_ADULT:
		quad = tooth // 10
		pos = tooth % 10
		labels[str(tooth)] = {
			"ar": f"{_FDI_POSITION_AR.get(pos, 'سن')} {_FDI_QUADRANT_AR.get(quad, '')}".strip(),
			"en": f"{_FDI_QUADRANT_EN.get(quad, '')} {_FDI_POSITION_EN.get(pos, 'Tooth')}".strip(),
		}
	return labels


TOOTH_LABELS_FDI: dict[str, dict] = _build_tooth_labels()


def _default_dental_warehouse(company: str) -> str | None:
	return default_department_warehouse(company, ["%Dental%", "%Clinic%", "DEMO-HC%"])


def _lesson_status(patient: str | None, tooth_id: str, lesson_id: str) -> str:
	if not patient:
		return "available"
	done = frappe.db.exists(
		"Healthcare Dental Chart Entry",
		{"patient": patient, "tooth_id": tooth_id, "treatment_plan": ["like", f"%{lesson_id}%"]},
	)
	return "completed" if done else "available"


@frappe.whitelist()
def get_dental_desk_dashboard(
	company: str | None = None,
	branch: str | None = None,
	patient: str | None = None,
	academic_year: int = 1,
) -> dict:
	company, branch = resolve_company_branch(company, branch)
	warehouse = _default_dental_warehouse(company)
	year = max(1, min(int(academic_year or 1), 5))

	today_date = getdate(today())
	appt_filters = {"branch": branch} if branch else {}
	today_appts = frappe.db.count(
		"Healthcare Appointment",
		{**appt_filters, "appointment_date": ["between", [f"{today_date} 00:00:00", f"{today_date} 23:59:59"]]},
	)
	active_cases = frappe.db.count(
		"Healthcare Dental Treatment Plan",
		{"company": company, "status": ["in", ["Draft", "Active", "In Progress"]]},
	)
	total_patients = frappe.db.count("Healthcare Patient", {"company": company})

	case_breakdown = frappe.db.sql(
		"""
		SELECT `condition` AS label, COUNT(*) AS cnt
		FROM `tabHealthcare Dental Chart Entry`
		GROUP BY `condition`
		ORDER BY cnt DESC
		LIMIT 6
		""",
		as_dict=True,
	)
	total_cases = sum(int(r.cnt) for r in case_breakdown) or 1
	for row in case_breakdown:
		row["pct"] = round(flt(row.cnt) / total_cases * 100, 1)

	chart = get_patient_dental_chart(patient, "FDI") if patient else {"entries": [], "tooth_map": {"teeth": FDI_ADULT}}
	entries_map = {str(e["tooth_id"]): e for e in chart.get("entries", [])}

	teeth_ui = []
	for tooth in FDI_ADULT:
		tid = str(tooth)
		lessons = DENTAL_CURRICULUM.get(year, {}).get(tid, [])
		entry = entries_map.get(tid)
		label = TOOTH_LABELS_FDI.get(tid, {"ar": f"سن {tid}", "en": f"Tooth {tid}"})
		lesson_rows = []
		for les in lessons:
			st = _lesson_status(patient, tid, les["id"])
			item = frappe.db.get_value("Item", {"item_code": les.get("item_code")}, "name")
			lesson_rows.append(
				{
					**les,
					"status": st,
					"item": item,
					"stock": warehouse_qty(item, warehouse) if item and warehouse else 0,
				}
			)
		teeth_ui.append(
			{
				"tooth_id": tid,
				"label_ar": label["ar"],
				"label_en": label["en"],
				"condition": (entry or {}).get("condition", "healthy"),
				"lessons": lesson_rows,
				"has_lessons": bool(lesson_rows),
			}
		)

	year_lessons = []
	for les in YEAR_LESSONS.get(year, []):
		teeth_for_lesson = [str(t) for t in les.get("teeth", [])]
		statuses = [_lesson_status(patient, tid, les["id"]) for tid in teeth_for_lesson] if teeth_for_lesson else ["available"]
		st = "completed" if statuses and all(s == "completed" for s in statuses) else "available"
		year_lessons.append({**les, "teeth": teeth_for_lesson, "status": st})

	return {
		"company": company,
		"branch": branch,
		"warehouse": warehouse,
		"patient": patient,
		"academic_year": year,
		"kpis": {
			"total_patients": total_patients,
			"today_appointments": today_appts,
			"active_cases": active_cases,
			"today_procedures": frappe.db.count(
				"Healthcare Dental Chart Entry",
				{"modified": [">=", f"{today_date} 00:00:00"]},
			),
		},
		"case_breakdown": case_breakdown,
		"teeth": teeth_ui,
		"year_lessons": year_lessons,
		"upper_teeth": [t for t in FDI_ADULT if 11 <= t <= 28],
		"lower_teeth": [t for t in FDI_ADULT if 31 <= t <= 48],
		"stock_rows": get_stock_rows(company, warehouse, "DEMO-HC-", 20),
		"accounts": get_accounts_summary(company, branch),
		"purchases": get_purchases_summary(company),
	}


@frappe.whitelist()
def complete_dental_lesson(
	patient: str,
	tooth_id: str,
	lesson_id: str,
	company: str | None = None,
	branch: str | None = None,
	condition: str = "filled",
) -> dict:
	company, branch = resolve_company_branch(company, branch)
	lesson = None
	tooth_for_lesson = str(tooth_id)
	for year_lessons in DENTAL_CURRICULUM.values():
		for tid, rows in year_lessons.items():
			if tid == str(tooth_id):
				for row in rows:
					if row["id"] == lesson_id:
						lesson = row
						break
	if not lesson:
		for rows in YEAR_LESSONS.values():
			for row in rows:
				if row["id"] == lesson_id:
					lesson = row
					teeth = row.get("teeth") or []
					if teeth and str(tooth_id) not in [str(t) for t in teeth]:
						tooth_for_lesson = str(teeth[0])
					break
	if not lesson:
		frappe.throw(_("Lesson not found for this tooth."))

	result = upsert_dental_chart_entry(
		patient=patient,
		tooth_id=tooth_for_lesson,
		company=company,
		branch=branch,
		condition=condition,
		numbering_system="FDI",
		treatment_plan=f"{lesson_id}: {lesson.get('title_en', '')}",
		status="completed",
	)

	# Link consumable stock issue if item exists
	warehouse = _default_dental_warehouse(company)
	item_name = frappe.db.get_value("Item", {"item_code": lesson.get("item_code")}, "name")
	stock_entry = None
	if item_name and warehouse and frappe.db.exists("DocType", "Stock Entry"):
		qty_on_hand = warehouse_qty(item_name, warehouse)
		if qty_on_hand >= 1:
			se = frappe.new_doc("Stock Entry")
			se.company = company
			se.posting_date = today()
			se.purpose = "Material Issue"
			se.remarks = _("Dental lesson consumable: {0}").format(lesson_id)
			item_doc = frappe.get_doc("Item", item_name)
			se.append(
				"items",
				{
					"item": item_name,
					"item_code": item_doc.item_code,
					"qty": 1,
					"s_warehouse": warehouse,
					"uom": item_doc.stock_uom,
				},
			)
			se.insert(ignore_permissions=True)
			se.submit()
			stock_entry = se.name

	return {**result, "lesson_id": lesson_id, "stock_entry": stock_entry, "item_code": item_code(item_name) if item_name else None}
