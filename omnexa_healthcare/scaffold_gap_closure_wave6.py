# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Scaffold DocType JSON + controller stubs for gap closure wave 6."""

from __future__ import annotations

import json

from omnexa_healthcare.scaffold_gap_closure_wave2 import (
	DOCTYPE_ROOT,
	_slug,
	build_controller_py,
	build_doctype_json,
)
from omnexa_healthcare.gap_closure_wave6_defs import GAP_CLOSURE_WAVE6_DOCTYPES


def _build_wave6_json(spec: dict) -> dict:
	doc = build_doctype_json(spec)
	if spec.get("istable"):
		doc["istable"] = 1
		doc["editable_grid"] = 1
		doc["permissions"] = [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
	return doc


def scaffold_all() -> list[str]:
	created: list[str] = []
	for spec in GAP_CLOSURE_WAVE6_DOCTYPES:
		slug = _slug(spec["name"])
		folder = DOCTYPE_ROOT / slug
		folder.mkdir(parents=True, exist_ok=True)
		json_path = folder / f"{slug}.json"
		py_path = folder / f"{slug}.py"
		json_path.write_text(json.dumps(_build_wave6_json(spec), indent="\t") + "\n", encoding="utf-8")
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
