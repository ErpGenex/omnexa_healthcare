# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Flexible physician compensation — dynamic % by service type, discounts, auto ledger."""

from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

SERVICE_CATEGORIES = (
	"Consultation",
	"Follow-up",
	"Procedure",
	"Surgery",
	"Emergency",
	"Lab",
	"Radiology",
	"Package",
	"Other",
)


@dataclass
class CompensationTier:
	service_category: str
	share_percent: float
	fixed_amount: float
	calculation_base: str
	discount_handling: str
	physician_discount_share_percent: float
	min_physician_share: float
	max_physician_share: float
	rule_name: str | None = None


def _compensation_enabled() -> bool:
	try:
		return bool(frappe.db.get_single_value("Healthcare Settings", "enable_physician_compensation"))
	except Exception:
		return False


def _line_gross(line) -> float:
	return flt(line.qty) * flt(line.rate)


def _line_discount(line, gross: float) -> float:
	if flt(line.patient_discount_amount):
		return flt(line.patient_discount_amount)
	if flt(line.patient_discount_percent):
		return gross * flt(line.patient_discount_percent) / 100
	return 0.0


def _resolve_specialty(charge_doc, line) -> str | None:
	if line.practitioner:
		rows = frappe.get_all(
			"Healthcare Practitioner Branch",
			filters={"parent": line.practitioner, "branch": charge_doc.branch, "is_active": 1},
			pluck="specialty",
			limit=1,
		)
		if rows:
			return rows[0]
	if charge_doc.encounter:
		return frappe.db.get_value("Healthcare Encounter", charge_doc.encounter, "specialty")
	return None


def resolve_compensation_tier(
	practitioner: str,
	company: str,
	branch: str,
	service_category: str,
	specialty: str | None = None,
	posting_date: str | None = None,
) -> CompensationTier | None:
	posting_date = getdate(posting_date or today())
	filters = {
		"practitioner": practitioner,
		"company": company,
		"branch": branch,
		"is_active": 1,
		"effective_from": ("<=", posting_date),
	}
	rules = frappe.get_all(
		"Healthcare Physician Compensation Rule",
		filters=filters,
		fields=["name", "specialty", "priority", "share_percent", "fixed_amount", "default_calculation_base", "default_discount_handling"],
		order_by="priority desc, modified desc",
	)
	candidates = []
	for rule in rules:
		if rule.specialty and specialty and rule.specialty != specialty:
			continue
		if rule.specialty and not specialty:
			continue
		candidates.append(rule)
	if not candidates:
		fallback_pct = frappe.db.get_value("Healthcare Practitioner", practitioner, "default_consultation_share_percent")
		if fallback_pct:
			return CompensationTier(
				service_category=service_category,
				share_percent=flt(fallback_pct),
				fixed_amount=0,
				calculation_base="Gross",
				discount_handling="Hospital Absorbs Discount",
				physician_discount_share_percent=0,
				min_physician_share=0,
				max_physician_share=0,
			)
		return None

	rule_name = candidates[0].name
	rule_doc = frappe.get_doc("Healthcare Physician Compensation Rule", rule_name)
	tier_row = None
	for row in rule_doc.tiers or []:
		if row.service_category == service_category:
			tier_row = row
			break

	if tier_row:
		return CompensationTier(
			service_category=service_category,
			share_percent=flt(tier_row.share_percent),
			fixed_amount=flt(tier_row.fixed_amount),
			calculation_base=tier_row.calculation_base or rule_doc.default_calculation_base or "Gross",
			discount_handling=tier_row.discount_handling or rule_doc.default_discount_handling or "Hospital Absorbs Discount",
			physician_discount_share_percent=flt(tier_row.physician_discount_share_percent),
			min_physician_share=flt(tier_row.min_physician_share),
			max_physician_share=flt(tier_row.max_physician_share),
			rule_name=rule_name,
		)

	return CompensationTier(
		service_category=service_category,
		share_percent=flt(rule_doc.share_percent),
		fixed_amount=flt(rule_doc.fixed_amount),
		calculation_base=rule_doc.default_calculation_base or "Gross",
		discount_handling=rule_doc.default_discount_handling or "Hospital Absorbs Discount",
		physician_discount_share_percent=0,
		min_physician_share=0,
		max_physician_share=0,
		rule_name=rule_name,
	)


def calculate_physician_share(gross: float, discount: float, tier: CompensationTier) -> dict:
	gross = flt(gross)
	discount = flt(discount)
	net = max(gross - discount, 0)

	if tier.discount_handling == "Fixed Physician Amount" and tier.fixed_amount:
		physician = flt(tier.fixed_amount)
	elif tier.fixed_amount and not tier.share_percent:
		physician = flt(tier.fixed_amount)
	else:
		base = gross
		if tier.calculation_base == "Net After Discount":
			base = net
		elif tier.calculation_base == "Collected":
			base = net
		physician = base * flt(tier.share_percent) / 100

		if tier.discount_handling == "Physician Absorbs Discount":
			physician = max(physician - discount, 0)
		elif tier.discount_handling == "Split Discount" and discount:
			physician -= discount * flt(tier.physician_discount_share_percent) / 100

	if tier.min_physician_share:
		physician = max(physician, flt(tier.min_physician_share))
	if tier.max_physician_share:
		physician = min(physician, flt(tier.max_physician_share))

	physician = flt(physician, 2)
	hospital = flt(max(net - physician, 0), 2)
	return {
		"gross_amount": gross,
		"patient_discount": discount,
		"net_amount": net,
		"physician_share": physician,
		"hospital_share": hospital,
		"calculation_base": tier.calculation_base,
		"discount_handling": tier.discount_handling,
		"compensation_rule": tier.rule_name,
	}


def preview_line_compensation(charge_doc, line) -> dict:
	if not line.practitioner:
		return {"physician_share": 0}
	gross = _line_gross(line)
	discount = _line_discount(line, gross)
	tier = resolve_compensation_tier(
		line.practitioner,
		charge_doc.company,
		charge_doc.branch,
		line.service_category or "Consultation",
		_resolve_specialty(charge_doc, line),
		charge_doc.posting_date,
	)
	if not tier:
		return {"physician_share": 0, "reason": "no_rule"}
	return calculate_physician_share(gross, discount, tier)


def apply_line_compensation_preview(charge_doc) -> None:
	if not _compensation_enabled():
		return
	for line in charge_doc.items or []:
		if not line.practitioner:
			line.physician_share = 0
			continue
		result = preview_line_compensation(charge_doc, line)
		line.physician_share = flt(result.get("physician_share"))


def accrue_from_service_charge(service_charge: str, sales_invoice: str | None = None) -> list[str]:
	if not _compensation_enabled():
		return []
	doc = frappe.get_doc("Healthcare Service Charge", service_charge)
	if doc.status not in ("Invoiced", "Draft"):
		return []
	created: list[str] = []
	for line in doc.items or []:
		if not line.practitioner:
			continue
		existing = frappe.db.exists(
			"Healthcare Physician Ledger Entry",
			{
				"service_charge": doc.name,
				"service_charge_line": line.idx,
				"status": ("!=", "Reversed"),
			},
		)
		if existing:
			continue
		result = preview_line_compensation(doc, line)
		if not flt(result.get("physician_share")) and not result.get("compensation_rule"):
			continue
		entry = frappe.get_doc(
			{
				"doctype": "Healthcare Physician Ledger Entry",
				"posting_date": doc.posting_date,
				"practitioner": line.practitioner,
				"patient": doc.patient,
				"service_category": line.service_category or "Consultation",
				"service_charge": doc.name,
				"service_charge_line": line.idx,
				"sales_invoice": sales_invoice or doc.sales_invoice,
				"compensation_rule": result.get("compensation_rule"),
				"gross_amount": result.get("gross_amount"),
				"patient_discount": result.get("patient_discount"),
				"net_amount": result.get("net_amount"),
				"physician_share": result.get("physician_share"),
				"hospital_share": result.get("hospital_share"),
				"calculation_base": result.get("calculation_base"),
				"discount_handling": result.get("discount_handling"),
				"status": "Accrued",
				"company": doc.company,
				"branch": doc.branch,
			}
		)
		entry.flags.ignore_branch_access = True
		entry.insert(ignore_permissions=True)
		created.append(entry.name)
	if created:
		frappe.db.commit()
	return created


@frappe.whitelist()
def calculate_settlement_preview(practitioner: str, gross_revenue: float, branch: str | None = None) -> dict:
	"""Backward-compatible preview — uses Consultation tier when available."""
	company = frappe.db.get_value("Branch", branch, "company") if branch else frappe.defaults.get_user_default("Company")
	tier = resolve_compensation_tier(
		practitioner,
		company,
		branch,
		"Consultation",
		None,
		today(),
	)
	if not tier:
		frappe.throw(_("No active compensation rule for practitioner {0}").format(practitioner))
	result = calculate_physician_share(flt(gross_revenue), 0, tier)
	return {
		"gross_revenue": flt(gross_revenue),
		"physician_share": result["physician_share"],
		"model": tier.discount_handling,
		"service_category": "Consultation",
	}


@frappe.whitelist()
def get_practitioner_ledger_summary(practitioner: str, branch: str | None = None) -> dict:
	filters = {"practitioner": practitioner, "status": "Accrued"}
	if branch:
		filters["branch"] = branch
	rows = frappe.get_all(
		"Healthcare Physician Ledger Entry",
		filters=filters,
		fields=["service_category", "physician_share", "gross_amount", "patient_discount"],
	)
	total = sum(flt(r.physician_share) for r in rows)
	by_cat: dict[str, float] = {}
	for r in rows:
		by_cat[r.service_category] = by_cat.get(r.service_category, 0) + flt(r.physician_share)
	return {"accrued_total": total, "entry_count": len(rows), "by_category": by_cat}
