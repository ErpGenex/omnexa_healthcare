# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""DocType definitions for final gap closure wave 5 (ICD-11 terminology)."""

from __future__ import annotations

GAP_CLOSURE_WAVE5_DOCTYPES: list[dict] = [
	{
		"name": "Healthcare Icd11 Code",
		"autoname": "field:code",
		"fields": [
			("code", "Data", "ICD-11 Code", {"reqd": 1, "unique": 1, "in_list_view": 1}),
			("description", "Data", "Description", {"reqd": 1, "in_list_view": 1}),
			("chapter", "Data", "Chapter", {"in_list_view": 1}),
			("icd10_map", "Data", "ICD-10 map (optional)", {"description": "Equivalent ICD-10 code when mapped"}),
			("is_active", "Check", "Active", {"default": "1", "in_list_view": 1}),
		],
	},
]

DEFAULT_ICD11_CODES: list[tuple[str, str, str, str | None]] = [
	("5A11", "Type 2 diabetes mellitus", "Endocrine", "E11"),
	("BA00", "Essential hypertension", "Circulatory", "I10"),
	("1F42", "COVID-19, virus identified", "Infectious", "U07.1"),
	("QA00", "Fracture of femur", "Injury", "S72"),
	("MD11", "Single episode major depressive disorder", "Mental", "F32"),
	("CA40", "Acute myocardial infarction", "Circulatory", "I21"),
	("DA22", "Asthma", "Respiratory", "J45"),
	("GB61", "Chronic kidney disease, stage 3", "Genitourinary", "N18.3"),
	("5A14", "Type 1 diabetes mellitus", "Endocrine", "E10"),
	("DB94", "Pneumonia", "Respiratory", "J18"),
]
