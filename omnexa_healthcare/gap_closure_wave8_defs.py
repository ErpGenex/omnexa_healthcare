# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Wave 8 — CDSS seed rules + SNOMED subset expansion."""

from __future__ import annotations

DEFAULT_CDS_RULES: list[tuple[str, str, str, str]] = [
	("High potassium with ACE inhibitor", "Medication Order", "lisinopril", "Critical"),
	("Warfarin + NSAID bleed risk", "Medication Order", "ibuprofen", "Contraindicated"),
	("Duplicate statin therapy", "Medication Order", "atorvastatin", "Warning"),
]

SNOMED_WAVE8_SUBSET: list[tuple[str, str]] = [
	("73211009", "Diabetes mellitus"),
	("38341003", "Hypertensive disorder"),
	("22298006", "Myocardial infarction"),
	("363346000", "Malignant neoplastic disease"),
	("195967001", "Asthma"),
	("13645005", "Chronic obstructive lung disease"),
	("44054006", "Diabetes mellitus type 2"),
	("237602007", "Metabolic syndrome X"),
	("414545008", "Ischemic heart disease"),
	("87433001", "Pulmonary embolism"),
]
