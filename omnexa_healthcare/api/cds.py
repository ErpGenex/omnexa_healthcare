# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Clinical Decision Support — 12-check eRx safety engine."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today


@frappe.whitelist()
def evaluate_cds(trigger_event: str, context: str | dict) -> list[dict]:
	data = frappe.parse_json(context) if isinstance(context, str) else (context or {})
	rules = frappe.get_all(
		"Healthcare Clinical Cds Rule",
		filters={"is_active": 1, "trigger_event": trigger_event},
		fields=["rule_name", "match_field", "severity", "message"],
	)
	alerts = []
	value = str(data.get("value") or data.get("item") or data.get("medication") or data.get("code") or "")
	for rule in rules:
		if rule.match_field and rule.match_field not in value:
			continue
		alerts.append({**rule, "check_type": "Other"})
		if rule.severity == "Contraindicated":
			break
	return alerts


@frappe.whitelist()
def evaluate_medication_order(patient: str, medication: str) -> list[dict]:
	return evaluate_erx_cds(patient, [{"drug_name": medication}])


@frappe.whitelist()
def evaluate_erx_cds(patient: str, items: str | list) -> list[dict]:
	"""Run 12 CDS checks for ePrescription order entry."""
	if isinstance(items, str):
		items = frappe.parse_json(items)
	alerts: list[dict] = []
	meta = frappe.get_meta("Healthcare Patient")
	optional = ["gender", "birth_date", "pregnancy_status", "lactation_status", "renal_function", "hepatic_function"]
	fields = [f for f in optional if meta.has_field(f)]
	patient_row = frappe.db.get_value("Healthcare Patient", patient, fields, as_dict=True) if fields else {}
	age_years = _patient_age_years(patient_row.get("birth_date"))
	active_meds = frappe.get_all(
		"Healthcare Medication Statement",
		filters={"patient": patient, "status": ["in", ["active", "on-hold"]]},
		pluck="medication_text",
	)
	allergies = frappe.get_all(
		"Healthcare Allergy Intolerance",
		filters={"patient": patient, "clinical_status": "active"},
		fields=["substance_text", "criticality"],
	)
	conditions = frappe.get_all(
		"Healthcare Clinical Condition",
		filters={"patient": patient, "clinical_status": ["in", ["Active", "Recurrence"]]},
		pluck="clinical_description",
	)
	seen_drugs: set[str] = set()

	for row in items:
		drug = (row.get("drug_name") or row.get("medication") or "").strip()
		if not drug:
			continue
		rxnorm = row.get("rxnorm_code")
		formulary = _get_formulary(drug, rxnorm)

		# Drug-drug
		from omnexa_healthcare.api.pharmacy import api_check_drug_interactions

		for hit in api_check_drug_interactions(patient, drug) or []:
			alerts.append(
				{
					"check_type": "Drug-Drug",
					"severity": hit.get("severity") or "Warning",
					"message": hit.get("description") or _("Drug interaction detected"),
				}
			)

		# Drug-allergy
		for allergy in allergies:
			substance = allergy.substance_text or ""
			if substance and substance.lower() in drug.lower():
				alerts.append(
					{
						"check_type": "Drug-Allergy",
						"severity": "Contraindicated",
						"message": _("Allergy to {0}").format(substance),
					}
				)

		# Drug-disease
		for cond in conditions:
			if cond and _disease_contraindication(drug, cond):
				alerts.append(
					{
						"check_type": "Drug-Disease",
						"severity": "Critical",
						"message": _("Caution: {0} with condition {1}").format(drug, cond),
					}
				)

		# Pregnancy / lactation
		if patient_row.get("gender") == "female":
			if patient_row.get("pregnancy_status") == "Pregnant" and formulary and formulary.pregnancy_category in ("D", "X"):
				alerts.append(
					{
						"check_type": "Pregnancy",
						"severity": "Contraindicated",
						"message": _("Pregnancy category {0} — {1}").format(formulary.pregnancy_category, drug),
					}
				)
			if patient_row.get("lactation_status") == "Yes" and _lactation_unsafe(drug):
				alerts.append(
					{
						"check_type": "Lactation",
						"severity": "Critical",
						"message": _("Lactation safety concern for {0}").format(drug),
					}
				)

		# Pediatric / geriatric
		if age_years is not None:
			if age_years < 18 and _pediatric_caution(drug):
				alerts.append(
					{
						"check_type": "Pediatric",
						"severity": "Warning",
						"message": _("Pediatric dosing review required for {0}").format(drug),
					}
				)
			if age_years >= 65 and _geriatric_caution(drug):
				alerts.append(
					{
						"check_type": "Geriatric",
						"severity": "Warning",
						"message": _("Beers criteria — use with caution: {0}").format(drug),
					}
				)

		# Renal / hepatic
		if patient_row.get("renal_function") in ("Impaired", "ESRD") and formulary and formulary.renal_adjustment_notes:
			alerts.append(
				{
					"check_type": "Renal",
					"severity": "Warning",
					"message": formulary.renal_adjustment_notes,
				}
			)
		if patient_row.get("hepatic_function") in ("Impaired", "Cirrhosis") and formulary and formulary.hepatic_adjustment_notes:
			alerts.append(
				{
					"check_type": "Hepatic",
					"severity": "Warning",
					"message": formulary.hepatic_adjustment_notes,
				}
			)

		# Duplicate therapy
		key = drug.lower()
		if key in seen_drugs or drug in active_meds:
			alerts.append(
				{
					"check_type": "Duplicate",
					"severity": "Warning",
					"message": _("Duplicate therapy: {0}").format(drug),
				}
			)
		seen_drugs.add(key)

		# Max dose
		if formulary and formulary.max_daily_dose:
			qty = float(row.get("quantity") or 1)
			if qty > formulary.max_daily_dose:
				alerts.append(
					{
						"check_type": "Max Dose",
						"severity": "Critical",
						"message": _("Exceeds max daily dose ({0}) for {1}").format(formulary.max_daily_dose, drug),
					}
				)

	return alerts


@frappe.whitelist()
def override_cds_alert(alert_log: str, reason: str) -> dict:
	if not reason:
		frappe.throw(_("Override reason is required."))
	frappe.db.set_value(
		"Healthcare Cds Alert Log",
		alert_log,
		{"overridden": 1, "override_reason": reason, "overridden_by": frappe.session.user},
	)
	return {"ok": True, "alert_log": alert_log}


def _patient_age_years(birth_date) -> int | None:
	if not birth_date:
		return None
	return int(date_diff(today(), getdate(birth_date)) / 365.25)


def _get_formulary(drug: str, rxnorm: str | None):
	if rxnorm:
		row = frappe.db.get_value(
			"Healthcare Drug Formulary",
			{"rxnorm_code": rxnorm, "is_active": 1},
			["pregnancy_category", "max_daily_dose", "renal_adjustment_notes", "hepatic_adjustment_notes"],
			as_dict=True,
		)
		if row:
			return frappe._dict(row)
	return frappe.db.get_value(
		"Healthcare Drug Formulary",
		{"drug_name": drug, "is_active": 1},
		["pregnancy_category", "max_daily_dose", "renal_adjustment_notes", "hepatic_adjustment_notes"],
		as_dict=True,
	)


def _disease_contraindication(drug: str, condition: str) -> bool:
	pairs = [
		("metformin", "renal"),
		("warfarin", "bleed"),
		("insulin", "hypoglyc"),
	]
	dl = drug.lower()
	cl = condition.lower()
	return any(d in dl and c in cl for d, c in pairs)


def _lactation_unsafe(drug: str) -> bool:
	return any(x in drug.lower() for x in ("codeine", "morphine", "aspirin"))


def _pediatric_caution(drug: str) -> bool:
	return any(x in drug.lower() for x in ("aspirin", "tetracycline", "fluoroquinolone"))


def _geriatric_caution(drug: str) -> bool:
	return any(x in drug.lower() for x in ("benzodiazepine", "diphenhydramine", "meperidine", "promethazine"))
