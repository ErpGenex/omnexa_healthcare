# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""openEHR composition bridge (EHRbase-compatible export)."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def export_openehr_composition(encounter: str) -> dict:
	"""Export encounter as openEHR-style composition JSON."""
	if not frappe.db.exists("Healthcare Encounter", encounter):
		frappe.throw(_("Encounter not found."), title=_("openEHR"))
	enc = frappe.get_doc("Healthcare Encounter", encounter)
	return {
		"_type": "COMPOSITION",
		"name": {"value": enc.name},
		"uid": {"value": enc.name},
		"language": {"code_string": "en"},
		"territory": {"code_string": "SA"},
		"category": {"value": "event", "defining_code": {"code_string": "433"}},
		"composer": {"name": enc.practitioner},
		"context": {
			"start_time": {"value": str(enc.period_start or enc.creation)},
			"setting": {"value": "other care", "defining_code": {"code_string": "238"}},
		},
		"content": [
			{
				"_type": "OBSERVATION",
				"name": {"value": "Chief Complaint"},
				"data": {
					"events": [
						{
							"data": {
								"items": [
									{"name": {"value": "Complaint"}, "value": {"value": enc.chief_complaint or ""}},
									{"name": {"value": "Status"}, "value": {"value": enc.status or ""}},
								]
							}
						}
					]
				},
			}
		],
		"source": "omnexa_healthcare",
		"fhir_encounter": enc.name,
	}
