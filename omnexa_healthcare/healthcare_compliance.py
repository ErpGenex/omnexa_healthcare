# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare compliance matrix — Epic parity 4.82."""

from __future__ import annotations

import frappe

from omnexa_healthcare.healthcare_epic_benchmark import EPIC_PARITY_MATRIX, get_epic_parity_score
from omnexa_healthcare.healthcare_global_leader import GLOBAL_LEADER_MATRIX, get_global_leader_score

HEALTHCARE_COMPLIANCE_MATRIX: list[dict] = GLOBAL_LEADER_MATRIX


@frappe.whitelist()
def get_healthcare_compliance_score() -> dict:
	out = get_global_leader_score()
	out["max_score"] = 5.0
	out["world_class_gate"] = out["weighted_score"] >= 4.5
	out["epic_parity_gate"] = out["weighted_score"] >= 4.82
	out["global_leader_gate"] = out.get("global_leader_gate", False)
	return out
