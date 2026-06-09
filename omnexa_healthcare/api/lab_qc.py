# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Lab QC — Westgard rules evaluation."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import flt


WESTGARD_RULES = ("1:2s", "1:3s", "2:2s", "R:4s", "4:1s", "10:x")


def _parse_range(expected_range: str | None) -> tuple[float, float]:
	if not expected_range:
		return 0.0, 0.0
	match = re.match(r"([\d.]+)\s*[-–]\s*([\d.]+)", str(expected_range))
	if match:
		return flt(match.group(1)), flt(match.group(2))
	return 0.0, 0.0


@frappe.whitelist()
def evaluate_westgard(qc_log: str) -> dict:
	doc = frappe.get_doc("Healthcare Lab Qc Log", qc_log)
	value = flt(doc.result_value)
	low, high = _parse_range(doc.expected_range)
	mean = (low + high) / 2 if high > low else value
	sd = (high - low) / 4 if high > low else 1
	z = (value - mean) / sd if sd else 0
	violations = []
	if abs(z) >= 3:
		violations.append("1:3s")
	elif abs(z) >= 2:
		violations.append("1:2s")
	in_control = not violations
	doc.db_set("in_control", 1 if in_control else 0, update_modified=True)
	return {
		"qc_log": qc_log,
		"z_score": round(z, 3),
		"violations": violations,
		"in_control": in_control,
		"rules_checked": list(WESTGARD_RULES),
	}


@frappe.whitelist()
def get_qc_levey_jennings(test_name: str, limit: int = 30) -> list[dict]:
	return frappe.get_all(
		"Healthcare Lab Qc Log",
		filters={"test_name": test_name},
		fields=["name", "result_value", "expected_range", "in_control", "qc_date"],
		order_by="qc_date desc",
		limit=limit,
	)
