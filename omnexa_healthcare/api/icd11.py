# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ICD-11 terminology — lookup, validation, ICD-10 crosswalk."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def search_icd11_codes(query: str = "", limit: int = 20) -> list[dict]:
	limit = min(int(limit or 20), 100)
	filters: dict = {"is_active": 1}
	if query:
		filters["code"] = ["like", f"%{query.strip()}%"]
	rows = frappe.get_all(
		"Healthcare Icd11 Code",
		filters=filters,
		fields=["code", "description", "chapter", "icd10_map"],
		limit=limit,
		order_by="code asc",
	)
	if query and not rows:
		rows = frappe.get_all(
			"Healthcare Icd11 Code",
			filters={"is_active": 1, "description": ["like", f"%{query.strip()}%"]},
			fields=["code", "description", "chapter", "icd10_map"],
			limit=limit,
			order_by="code asc",
		)
	return rows


@frappe.whitelist()
def validate_icd11_code(code: str | None) -> dict:
	if not code:
		frappe.throw(_("ICD-11 code is required."))
	row = frappe.db.get_value(
		"Healthcare Icd11 Code",
		{"code": code, "is_active": 1},
		["code", "description", "icd10_map"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("ICD-11 code {0} is not in master or inactive.").format(code), title=_("ICD-11"))
	return row


@frappe.whitelist()
def map_icd11_to_icd10(code: str) -> dict:
	row = validate_icd11_code(code)
	return {"icd11": row.code, "icd10": row.icd10_map, "description": row.description}
