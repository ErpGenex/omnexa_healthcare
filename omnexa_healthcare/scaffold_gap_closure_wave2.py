# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Scaffold DocType JSON + controller stubs for gap closure wave 2."""

from __future__ import annotations

import json
from pathlib import Path

from omnexa_healthcare.gap_closure_wave2_defs import GAP_CLOSURE_WAVE2_DOCTYPES

APP_PATH = Path(__file__).resolve().parent
DOCTYPE_ROOT = APP_PATH / "omnexa_healthcare" / "doctype"


def _slug(name: str) -> str:
	return name.lower().replace(" ", "_")


def _field_entry(fieldname: str, fieldtype: str, label: str, extra: dict | None = None) -> dict:
	entry = {"fieldname": fieldname, "fieldtype": fieldtype, "label": label}
	if extra:
		entry.update(extra)
	return entry


def build_doctype_json(spec: dict) -> dict:
	field_order = [f[0] for f in spec["fields"]]
	fields = [_field_entry(*f) for f in spec["fields"]]
	doc = {
		"actions": [],
		"autoname": spec.get("autoname", "naming_series:"),
		"doctype": "DocType",
		"engine": "InnoDB",
		"field_order": field_order,
		"fields": fields,
		"index_web_pages_for_search": 1,
		"links": [],
		"modified": "2026-06-06 12:00:00",
		"modified_by": "Administrator",
		"module": "Omnexa Healthcare",
		"name": spec["name"],
		"owner": "Administrator",
		"permissions": [
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "report": 1},
			{"role": "Company Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "report": 1},
			{"role": "Desk User", "read": 1, "write": 1, "create": 1, "export": 1, "report": 1},
		],
		"sort_field": "modified",
		"sort_order": "DESC",
		"states": [],
		"track_changes": 1,
	}
	return doc


def build_controller_py(class_name: str) -> str:
	return f"""# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.model.document import Document


class {class_name}(Document):
\tpass
"""


def scaffold_all() -> list[str]:
	created: list[str] = []
	for spec in GAP_CLOSURE_WAVE2_DOCTYPES:
		slug = _slug(spec["name"])
		folder = DOCTYPE_ROOT / slug
		folder.mkdir(parents=True, exist_ok=True)
		json_path = folder / f"{slug}.json"
		py_path = folder / f"{slug}.py"
		json_path.write_text(json.dumps(build_doctype_json(spec), indent="\t") + "\n", encoding="utf-8")
		class_name = spec["name"].replace(" ", "")
		if not py_path.exists():
			py_path.write_text(build_controller_py(class_name), encoding="utf-8")
		init_path = folder / "__init__.py"
		if not init_path.exists():
			init_path.write_text("", encoding="utf-8")
		created.append(spec["name"])
	return created


if __name__ == "__main__":
	for name in scaffold_all():
		print(f"Scaffolded: {name}")
