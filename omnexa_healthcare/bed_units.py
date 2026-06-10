# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Bed type ↔ service unit compatibility for IPD, ICU, NICU, and companion lodging."""

from __future__ import annotations

COMPANION_BED_TYPES = frozenset({"Companion"})
CRITICAL_CARE_BED_TYPES = frozenset({"ICU", "HDU", "NICU", "Nursery"})
NEONATAL_BED_TYPES = frozenset({"NICU", "Nursery"})

UNIT_BED_TYPES: dict[str, frozenset[str]] = {
	"ICU": frozenset({"ICU", "HDU"}),
	"NICU": frozenset({"NICU", "Nursery", "Pediatric"}),
	"Companion Ward": frozenset({"Companion"}),
	"Ward": frozenset({"General", "Isolation", "Pediatric"}),
	"Emergency": frozenset({"General"}),
}


def allowed_bed_types_for_unit(unit_type: str | None) -> frozenset[str] | None:
	"""Return allowed bed types for a service unit, or None if any bed type is allowed."""
	if not unit_type:
		return None
	return UNIT_BED_TYPES.get(unit_type.strip())


def is_companion_bed(bed_type: str | None) -> bool:
	return (bed_type or "").strip() in COMPANION_BED_TYPES


def is_critical_care_bed(bed_type: str | None) -> bool:
	return (bed_type or "").strip() in CRITICAL_CARE_BED_TYPES


def is_neonatal_bed(bed_type: str | None) -> bool:
	return (bed_type or "").strip() in NEONATAL_BED_TYPES


def care_unit_for_bed(bed_type: str | None) -> str:
	bt = (bed_type or "").strip()
	if bt in NEONATAL_BED_TYPES:
		return "NICU"
	if bt in {"ICU", "HDU"}:
		return "ICU"
	return "General"
