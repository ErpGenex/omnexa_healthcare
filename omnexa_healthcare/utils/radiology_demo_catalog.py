# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Demo radiology study images bundled under /assets/omnexa_healthcare/images/demo-radiology/."""

from __future__ import annotations

DEMO_RAD_ASSET_BASE = "/assets/omnexa_healthcare/images/demo-radiology"

DEMO_RADIOLOGY_STUDIES: dict[str, dict] = {
	"chest-xray": {
		"title": "Chest X-Ray PA",
		"title_ar": "أشعة صدر",
		"modality": "XR",
		"image": f"{DEMO_RAD_ASSET_BASE}/chest-xray.svg",
		"findings": "Heart size within normal limits. Lungs clear. No pleural effusion (demo).",
		"conclusion": "No acute cardiopulmonary abnormality (demo).",
	},
	"ct-abdomen": {
		"title": "CT Abdomen",
		"title_ar": "أشعة مقطعية بطن",
		"modality": "CT",
		"image": f"{DEMO_RAD_ASSET_BASE}/ct-abdomen.svg",
		"findings": "Liver, spleen, and kidneys unremarkable. No free fluid (demo).",
		"conclusion": "Normal CT abdomen study (demo).",
	},
	"mri-brain": {
		"title": "MRI Brain",
		"title_ar": "رنين مغناطيسي دماغ",
		"modality": "MR",
		"image": f"{DEMO_RAD_ASSET_BASE}/mri-brain.svg",
		"findings": "No mass effect or midline shift. Ventricles normal (demo).",
		"conclusion": "Normal MRI brain (demo).",
	},
}

DEMO_RAD_ROTATION = ["chest-xray", "ct-abdomen", "mri-brain", "chest-xray"]


def demo_study_for_index(idx: int) -> dict:
	key = DEMO_RAD_ROTATION[idx % len(DEMO_RAD_ROTATION)]
	return {"key": key, **DEMO_RADIOLOGY_STUDIES[key]}
