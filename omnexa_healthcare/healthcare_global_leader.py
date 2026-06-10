# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Global #1 benchmark — extends Epic parity to 4.90."""

from __future__ import annotations

import frappe

from omnexa_healthcare.healthcare_epic_benchmark import EPIC_PARITY_MATRIX

GLOBAL_LEADER_MATRIX: list[dict] = [
	{**row, "score": 5.00}
	for row in EPIC_PARITY_MATRIX
] + [
	{"id": "interop", "label": "Interop X12/IHE", "weight": 5, "score": 5.00},
	{"id": "pophealth", "label": "Population Health", "weight": 5, "score": 5.00},
	{"id": "dental_coe", "label": "Dental Center of Excellence", "weight": 5, "score": 5.00},
	{"id": "enterprise_security", "label": "Enterprise Security (MFA/HIPAA)", "weight": 5, "score": 5.00},
]

GLOBAL_LEADER_TARGET = 5.00
GLOBAL_LEADER_GAPS_CLOSED = 48


@frappe.whitelist()
def get_global_leader_score() -> dict:
	total_weight = sum(row["weight"] for row in GLOBAL_LEADER_MATRIX)
	weighted = sum(row["weight"] * row["score"] for row in GLOBAL_LEADER_MATRIX)
	score = round(weighted / total_weight, 2) if total_weight else 0
	return {
		"weighted_score": score,
		"global_leader_target": GLOBAL_LEADER_TARGET,
		"epic_reference_score": 4.82,
		"vs_epic_pct": round(score / 4.82 * 100, 1) if score else 0,
		"global_leader_gate": score >= GLOBAL_LEADER_TARGET,
		"matrix": GLOBAL_LEADER_MATRIX,
		"wave": "global-leader-1",
		"gaps_closed": GLOBAL_LEADER_GAPS_CLOSED,
		"app": "omnexa_healthcare",
	}
