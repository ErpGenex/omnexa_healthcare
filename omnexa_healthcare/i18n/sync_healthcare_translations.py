# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Build omnexa_healthcare translation CSV files from DocTypes, workspace, pages, reports."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import frappe

from omnexa_healthcare.hooks import app_title
from omnexa_healthcare.i18n.healthcare_i18n_catalog import _has_untranslated_english, normalize_en, translate_to_ar
from omnexa_healthcare.terminology import PATIENT_TERMINOLOGY_AR, PATIENT_TERMINOLOGY_EN
from omnexa_healthcare.workspace.healthcare_workspace import REPORT_SECTIONS, WORKSPACE_SECTIONS

_TRANSLATIONS_DIR = Path(__file__).resolve().parents[1] / "translations"

# Extra strings from pages, hooks, validation messages (not in DocType meta).
_EXTRA_STRINGS: tuple[str, ...] = (
	app_title,
	"Healthcare",
	"Load file",
	"Select a patient",
	"Episodes of care",
	"Appointments",
	"Encounters",
	"Conditions (ICD-10)",
	"Vitals & observations",
	"Lab & imaging reports",
	"Admissions",
	"ER visits",
	"Birth date",
	"FHIR IPS document bundle loaded — international patient summary standard.",
	"Invoiced charges must reference a Sales Invoice.",
	"Branch {0} does not exist.",
	"Branch belongs to a different company.",
	"Patient does not exist.",
	"Patient must belong to the same company and branch.",
	"Patient billing account could not be resolved.",
	"Billing account belongs to a different company.",
	"Encounter patient must match.",
	"Admission patient must match.",
	"Admission must belong to the same company and branch.",
	"Row {0}: Item belongs to a different company.",
	"Full display name could not be built from name parts.",
	"Managing facility does not exist.",
	"Managing facility must belong to the same company and branch.",
	"Billing account does not exist.",
	"Billing account must belong to the same company.",
	"At least one identifier is required (e.g. MRN or national ID).",
	"Primary MRN applies only to rows with identifier type MRN.",
	"When an MRN is recorded, exactly one row must be marked as Primary MRN.",
	"Identifier value is required on each row.",
	"Duplicate identifier type and value combination.",
	"Telecom value is required on each row.",
	"Deceased date/time is required when deceased is checked.",
	"Online Healthcare Booking",
	"Book a service",
	"Confirm booking",
	"Published services",
	"Available slot",
	"First name",
	"Family name",
)


def collect_healthcare_strings() -> set[str]:
	strings: set[str] = set(_EXTRA_STRINGS)
	strings.update(PATIENT_TERMINOLOGY_EN.keys())
	strings.update(PATIENT_TERMINOLOGY_AR.keys())

	for sec, items in WORKSPACE_SECTIONS + REPORT_SECTIONS:
		strings.add(sec)
		for _, _, label in items:
			strings.add(label)

	for dt in frappe.get_all("DocType", filters={"module": "Omnexa Healthcare"}, pluck="name"):
		meta = frappe.get_meta(dt)
		strings.add(meta.name)
		if meta.name.startswith("Healthcare "):
			strings.add(meta.name[11:])
		for f in meta.fields:
			if f.label:
				strings.add(f.label)
			if f.options and f.fieldtype in ("Select", "Tab Break") and "\n" in str(f.options):
				for opt in f.options.split("\n"):
					if opt.strip():
						strings.add(opt.strip())

	for page in frappe.get_all("Page", filters={"module": "Omnexa Healthcare"}, pluck="name"):
		title = frappe.db.get_value("Page", page, "title") or page
		strings.add(title)
		label = page.replace("healthcare-", "").replace("-", " ").title()
		strings.add(label)

	for report in frappe.get_all("Report", filters={"module": "Omnexa Healthcare"}, pluck="name"):
		strings.add(report)
		if report.startswith("Healthcare "):
			strings.add(report[11:])

	return {s for s in strings if s and s.strip()}


def _read_existing_csv(path: Path) -> dict[str, str]:
	if not path.exists():
		return {}
	out: dict[str, str] = {}
	with path.open(encoding="utf-8", newline="") as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) >= 2 and row[0] and not row[0].startswith("#"):
				out[row[0]] = row[1]
	return out


def _write_csv(path: Path, rows: dict[str, str]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f, lineterminator="\n")
		for key in sorted(rows.keys(), key=lambda k: (k.lower(), k)):
			writer.writerow([key, rows[key]])


def build_translation_maps(
	existing_ar: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
	"""Return (ar_map, en_map, stats)."""
	existing_ar = dict(existing_ar or {})
	strings = collect_healthcare_strings()
	ar_rows: dict[str, str] = {}
	en_rows: dict[str, str] = {}
	stats = {"total": len(strings), "ar_translated": 0, "ar_manual": 0, "en_overrides": 0, "ar_untranslated": 0}

	for src in strings:
		en_val = normalize_en(src)
		if en_val != src:
			en_rows[src] = en_val
			stats["en_overrides"] += 1

		ar_val = translate_to_ar(src)
		ar_rows[src] = ar_val
		if ar_val != src:
			stats["ar_translated"] += 1
		else:
			stats["ar_untranslated"] += 1

	# Preserve legacy manual rows not discovered automatically (if high quality)
	for key, val in existing_ar.items():
		if key in ar_rows:
			continue
		if val and val != key and not _has_untranslated_english(val):
			ar_rows[key] = val
			stats["ar_manual"] += 1

	return ar_rows, en_rows, stats


def sync_healthcare_translations(*, write: bool = True) -> dict:
	"""Regenerate translations/ar.csv and translations/en.csv."""
	ar_path = _TRANSLATIONS_DIR / "ar.csv"
	en_path = _TRANSLATIONS_DIR / "en.csv"
	existing_ar = _read_existing_csv(ar_path)
	ar_rows, en_rows, stats = build_translation_maps(existing_ar)

	if write:
		_write_csv(ar_path, ar_rows)
		_write_csv(en_path, en_rows)
		frappe.clear_cache()

	stats["ar_total"] = len(ar_rows)
	stats["en_total"] = len(en_rows)
	stats["ar_path"] = str(ar_path)
	stats["en_path"] = str(en_path)
	return stats


def execute():
	stats = sync_healthcare_translations(write=True)
	print(
		f"Healthcare i18n: {stats['ar_total']} AR rows "
		f"({stats['ar_translated']} auto, {stats['ar_manual']} kept, "
		f"{stats['ar_untranslated']} still English), "
		f"{stats['en_total']} EN overrides"
	)
	if stats["ar_untranslated"]:
		print(f"Warning: {stats['ar_untranslated']} strings still untranslated — review ar.csv")
