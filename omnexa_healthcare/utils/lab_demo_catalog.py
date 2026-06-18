# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Laboratory demo catalog — panels, reference ranges, and printable result rows."""

from __future__ import annotations

from typing import Any

# (test_name, unit, low, high, demo_result)
LabTestSpec = tuple[str, str, float | None, float | None, str | float]

LabSection = tuple[str, str, list[LabTestSpec]]  # section_en, section_ar, tests

COMPREHENSIVE_LAB_SECTIONS: list[LabSection] = [
	(
		"Complete Blood Picture (CBC)",
		"صورة دم كاملة",
		[
			("WBCs", "10³/µL", 4.0, 11.0, 7.2),
			("RBCs", "10⁶/µL", 4.5, 5.9, 5.1),
			("Hemoglobin", "g/dL", 13.0, 17.0, 14.8),
			("Hematocrit", "%", 40.0, 52.0, 44.0),
			("MCV", "fL", 80.0, 100.0, 88.0),
			("MCH", "pg", 27.0, 33.0, 29.0),
			("MCHC", "g/dL", 32.0, 36.0, 34.0),
			("Platelets", "10³/µL", 150.0, 450.0, 265.0),
		],
	),
	(
		"Differential Count",
		"العد التفاضلي",
		[
			("Neutrophils", "%", 40.0, 75.0, 58.0),
			("Lymphocytes", "%", 20.0, 45.0, 32.0),
			("Monocytes", "%", 2.0, 10.0, 6.0),
			("Eosinophils", "%", 1.0, 6.0, 3.0),
			("Basophils", "%", 0.0, 2.0, 1.0),
		],
	),
	(
		"Kidney Function Tests",
		"وظائف الكلى",
		[
			("Urea", "mg/dL", 15.0, 45.0, 28.0),
			("Creatinine", "mg/dL", 0.7, 1.3, 0.9),
			("Uric Acid", "mg/dL", 3.5, 7.2, 5.8),
		],
	),
	(
		"Liver Function Tests",
		"وظائف الكبد",
		[
			("ALT (SGPT)", "U/L", 7.0, 56.0, 24.0),
			("AST (SGOT)", "U/L", 10.0, 40.0, 22.0),
			("Alkaline Phosphatase", "U/L", 44.0, 147.0, 78.0),
			("Total Bilirubin", "mg/dL", 0.1, 1.2, 0.7),
			("Direct Bilirubin", "mg/dL", 0.0, 0.3, 0.1),
			("Total Protein", "g/dL", 6.0, 8.3, 7.2),
			("Albumin", "g/dL", 3.5, 5.5, 4.4),
		],
	),
	(
		"Glucose & Lipid Profile",
		"سكر ودهون",
		[
			("Fasting Blood Sugar", "mg/dL", 70.0, 100.0, 92.0),
			("HbA1c", "%", 4.0, 5.6, 5.2),
			("Cholesterol (Total)", "mg/dL", None, 200.0, 178.0),
			("Triglycerides", "mg/dL", None, 150.0, 110.0),
			("HDL", "mg/dL", 40.0, None, 52.0),
			("LDL", "mg/dL", None, 130.0, 98.0),
		],
	),
]

LAB_DEMO_PANELS: dict[str, dict[str, Any]] = {
	"LAB-COMPLETE": {
		"panel_name": "Complete Laboratory Panel",
		"panel_name_ar": "تحاليل شاملة",
		"loinc": "24331-0",
		"sections": COMPREHENSIVE_LAB_SECTIONS,
	},
	"LAB-CBC": {
		"panel_name": "CBC Panel",
		"panel_name_ar": "صورة دم كاملة",
		"sections": [COMPREHENSIVE_LAB_SECTIONS[0], COMPREHENSIVE_LAB_SECTIONS[1]],
	},
	"LAB-KFT": {
		"panel_name": "Kidney Function Panel",
		"panel_name_ar": "وظائف الكلى",
		"sections": [COMPREHENSIVE_LAB_SECTIONS[2]],
	},
	"LAB-LFT": {
		"panel_name": "Liver Function Panel",
		"panel_name_ar": "وظائف الكبد",
		"sections": [COMPREHENSIVE_LAB_SECTIONS[3]],
	},
	"LAB-LIPID": {
		"panel_name": "Lipid Profile",
		"panel_name_ar": "دهون الدم",
		"sections": [
			(
				"Lipid Profile",
				"دهون الدم",
				[
					("Cholesterol (Total)", "mg/dL", None, 200.0, 178.0),
					("Triglycerides", "mg/dL", None, 150.0, 110.0),
					("HDL", "mg/dL", 40.0, None, 52.0),
					("LDL", "mg/dL", None, 130.0, 98.0),
				],
			)
		],
	},
	"LAB-GLU": {
		"panel_name": "Glucose Panel",
		"panel_name_ar": "سكر الدم",
		"sections": [
			(
				"Glucose",
				"سكر الدم",
				[
					("Fasting Blood Sugar", "mg/dL", 70.0, 100.0, 92.0),
					("Random Blood Sugar", "mg/dL", 70.0, 140.0, 118.0),
					("HbA1c", "%", 4.0, 5.6, 5.2),
				],
			)
		],
	},
	"LAB-TFT": {
		"panel_name": "Thyroid Function Panel",
		"panel_name_ar": "الغدة الدرقية",
		"sections": [
			(
				"Thyroid Function",
				"الغدة الدرقية",
				[
					("TSH", "µIU/mL", 0.4, 4.0, 2.1),
					("Free T4", "ng/dL", 0.8, 1.8, 1.2),
					("Free T3", "pg/mL", 2.3, 4.2, 3.1),
				],
			)
		],
	},
	"LAB-URINE": {
		"panel_name": "Urinalysis",
		"panel_name_ar": "تحليل بول",
		"sections": [
			(
				"Urinalysis",
				"تحليل بول",
				[
					("Color", "", None, None, "Yellow"),
					("Appearance", "", None, None, "Clear"),
					("pH", "", 5.0, 8.0, 6.0),
					("Protein", "", None, None, "Negative"),
					("Glucose", "", None, None, "Negative"),
					("Blood", "", None, None, "Negative"),
				],
			)
		],
	},
	"LAB-COAG": {
		"panel_name": "Coagulation Panel",
		"panel_name_ar": "تخثر الدم",
		"sections": [
			(
				"Coagulation",
				"تخثر الدم",
				[
					("PT", "sec", 11.0, 13.5, 12.2),
					("INR", "", 0.8, 1.2, 1.0),
					("APTT", "sec", 25.0, 35.0, 29.0),
				],
			)
		],
	},
	"LAB-IRON": {
		"panel_name": "Iron Studies",
		"panel_name_ar": "دراسة الحديد",
		"sections": [
			(
				"Iron Studies",
				"دراسة الحديد",
				[
					("Serum Iron", "µg/dL", 60.0, 170.0, 95.0),
					("TIBC", "µg/dL", 250.0, 450.0, 320.0),
					("Ferritin", "ng/mL", 30.0, 400.0, 145.0),
				],
			)
		],
	},
	"LAB-VITD": {
		"panel_name": "Vitamin D",
		"panel_name_ar": "فيتامين د",
		"sections": [
			(
				"Vitamins",
				"فيتامينات",
				[
					("Vitamin D (25-OH)", "ng/mL", 30.0, 100.0, 42.0),
					("Vitamin B12", "pg/mL", 200.0, 900.0, 450.0),
				],
			)
		],
	},
}

LAB_DEMO_ORDER_ROTATION: list[str] = list(LAB_DEMO_PANELS.keys())


def format_reference_range(low: float | None, high: float | None) -> str:
	if low is not None and high is not None:
		return f"{low:g} - {high:g}"
	if high is not None:
		return f"< {high:g}"
	if low is not None:
		return f"> {low:g}"
	return "—"


def is_abnormal_result(low: float | None, high: float | None, value: str | float) -> bool:
	if isinstance(value, str):
		return False
	try:
		num = float(value)
	except (TypeError, ValueError):
		return False
	if low is not None and num < low:
		return True
	if high is not None and num > high:
		return True
	return False


def demo_lab_result_rows(panel_code: str, patient: str | None = None) -> list[dict]:
	"""Build child-table rows for Healthcare Diagnostic Report.lab_results."""
	panel = LAB_DEMO_PANELS.get(panel_code) or LAB_DEMO_PANELS["LAB-COMPLETE"]
	rows: list[dict] = []
	# Slight variation per patient for demo realism
	offset = 0
	if patient:
		offset = sum(ord(c) for c in patient[-4:]) % 5 - 2

	for section_en, _section_ar, tests in panel.get("sections") or []:
		rows.append(
			{
				"section": section_en,
				"is_section_header": 1,
				"test_name": section_en,
				"result_value": "",
				"unit": "",
				"reference_range": "",
				"is_abnormal": 0,
			}
		)
		for test_name, unit, low, high, demo_val in tests:
			val = demo_val
			if isinstance(demo_val, (int, float)) and offset:
				val = round(float(demo_val) + offset * 0.3, 1)
			ref = format_reference_range(low, high)
			rows.append(
				{
					"section": section_en,
					"is_section_header": 0,
					"test_name": test_name,
					"result_value": str(val),
					"unit": unit,
					"reference_range": ref,
					"is_abnormal": 1 if is_abnormal_result(low, high, val) else 0,
				}
			)
	return rows


def panel_request_title(panel_code: str) -> str:
	panel = LAB_DEMO_PANELS.get(panel_code) or {}
	return panel.get("panel_name") or panel_code
