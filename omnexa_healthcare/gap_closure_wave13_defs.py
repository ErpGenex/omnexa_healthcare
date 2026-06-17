# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Wave 13 — Global #1 gap closure: patient registration gate + medical devices."""

from __future__ import annotations

GAP_CLOSURE_WAVE13_DOCTYPES: list[dict] = [
	{
		"name": "Healthcare Medical Device",
		"autoname": "format:HMD-{device_code}",
		"fields": [
			("device_code", "Data", "Device code", {"reqd": 1, "in_list_view": 1}),
			("device_name", "Data", "Device name", {"reqd": 1, "in_list_view": 1}),
			(
				"device_type",
				"Select",
				"Device type",
				{
					"options": "Vital Signs Monitor\nInfusion Pump\nVentilator\nDefibrillator\nPulse Oximeter\nECG\nLab Analyzer\nImaging Modality\nWearable RPM\nOther",
					"default": "Vital Signs Monitor",
					"in_list_view": 1,
				},
			),
			("manufacturer", "Data", "Manufacturer"),
			("model_number", "Data", "Model"),
			("serial_number", "Data", "Serial number"),
			(
				"integration_protocol",
				"Select",
				"Protocol",
				{
					"options": "HL7_ORU\nFHIR_Observation\nASTM\nDICOM\nMQTT\nREST_API",
					"default": "FHIR_Observation",
					"in_list_view": 1,
				},
			),
			("fhir_device_id", "Data", "FHIR Device ID"),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch"}),
			("status", "Select", "Status", {"options": "Active\nInactive\nMaintenance", "default": "Active", "in_list_view": 1}),
			("last_sync_at", "Datetime", "Last sync"),
		],
	},
]

GAP_CLOSURE_WAVE13_CHECKS: list[str] = [
	"registration_status",
	"portal_user",
	"Healthcare Medical Device",
	"omnexa_healthcare.api.patient_registration",
	"omnexa_healthcare.api.device_integration",
]
