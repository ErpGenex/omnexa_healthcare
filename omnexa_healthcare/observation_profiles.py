# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""LOINC / UCUM defaults for Healthcare Observation profiles."""

OBSERVATION_PROFILE_DEFAULTS: dict[str, dict] = {
	"heart_rate": {"loinc": "8867-4", "unit_ucum": "/min", "label": "Heart rate"},
	"spo2": {"loinc": "2708-6", "unit_ucum": "%", "label": "SpO2"},
	"body_temperature": {"loinc": "8310-5", "unit_ucum": "Cel", "label": "Body temperature"},
	"body_weight": {"loinc": "29463-7", "unit_ucum": "kg", "label": "Body weight"},
	"body_height": {"loinc": "8302-2", "unit_ucum": "cm", "label": "Body height"},
	"blood_pressure": {"loinc": "85354-9", "unit_ucum": "mm[Hg]", "label": "Blood pressure"},
	"lab_glucose": {"loinc": "2345-7", "unit_ucum": "mg/dL", "label": "Glucose"},
	"lab_hemoglobin": {"loinc": "718-7", "unit_ucum": "g/dL", "label": "Hemoglobin"},
}


def default_ucum_for_profile(profile: str) -> str | None:
	row = OBSERVATION_PROFILE_DEFAULTS.get(profile or "")
	return row.get("unit_ucum") if row else None
