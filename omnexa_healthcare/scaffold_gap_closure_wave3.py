# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import json
from pathlib import Path

from omnexa_healthcare.gap_closure_wave3_defs import GAP_CLOSURE_WAVE3_DOCTYPES
from omnexa_healthcare.scaffold_gap_closure_wave2 import build_controller_py, build_doctype_json

APP_PATH = Path(__file__).resolve().parent
DOCTYPE_ROOT = APP_PATH / "omnexa_healthcare" / "doctype"


def _slug(name: str) -> str:
	return name.lower().replace(" ", "_")


def scaffold_all() -> list[str]:
	created: list[str] = []
	for spec in GAP_CLOSURE_WAVE3_DOCTYPES:
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
