# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Rule-based patient symptom checker (AI-ready)."""

from __future__ import annotations

import frappe
from frappe import _

SYMPTOM_RULES: dict[str, dict] = {
	"fever": {"urgency": "medium", "specialty": "Internal Medicine", "advice": "Monitor temperature; seek care if >39°C or persistent."},
	"chest_pain": {"urgency": "high", "specialty": "Cardiology", "advice": "Seek emergency care immediately."},
	"shortness_of_breath": {"urgency": "high", "specialty": "Pulmonology", "advice": "Urgent evaluation recommended."},
	"cough": {"urgency": "low", "specialty": "Internal Medicine", "advice": "Rest and hydration; book if >7 days."},
	"headache": {"urgency": "low", "specialty": "Neurology", "advice": "OTC analgesics; urgent if sudden severe."},
	"abdominal_pain": {"urgency": "medium", "specialty": "Gastroenterology", "advice": "Book appointment; ER if severe."},
}


@frappe.whitelist(allow_guest=True)
def check_symptoms(symptoms: str | list) -> dict:
	"""Assess symptom list and suggest specialty / urgency."""
	if isinstance(symptoms, str):
		import json

		try:
			symptoms = json.loads(symptoms)
		except Exception:
			symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]
	if not symptoms:
		frappe.throw(_("Provide at least one symptom."), title=_("Symptom Checker"))
	normalized = [s.lower().replace(" ", "_") for s in symptoms]
	matches = []
	max_urgency = "low"
	urgency_rank = {"low": 0, "medium": 1, "high": 2}
	for sym in normalized:
		rule = SYMPTOM_RULES.get(sym)
		if rule:
			matches.append({"symptom": sym, **rule})
			if urgency_rank.get(rule["urgency"], 0) > urgency_rank.get(max_urgency, 0):
				max_urgency = rule["urgency"]
	specialty = matches[0]["specialty"] if matches else "General Practice"
	return {
		"symptoms": normalized,
		"matches": matches,
		"urgency": max_urgency,
		"suggested_specialty": specialty,
		"book_appointment": max_urgency in ("medium", "high"),
		"disclaimer": _("Not a diagnosis. Consult a licensed clinician."),
	}
