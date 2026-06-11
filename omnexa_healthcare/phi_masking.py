# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Field-level PHI masking for lists and guest contexts."""

from __future__ import annotations

import re


def mask_mobile(value: str | None) -> str:
	if not value:
		return ""
	digits = re.sub(r"\D", "", value)
	if len(digits) < 4:
		return "****"
	return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_email(value: str | None) -> str:
	if not value or "@" not in value:
		return value or ""
	local, domain = value.split("@", 1)
	masked_local = local[0] + "***" if local else "***"
	return f"{masked_local}@{domain}"


def mask_patient_row(row: dict, fields: tuple[str, ...] = ("mobile", "email", "phone")) -> dict:
	out = dict(row)
	for field in fields:
		if field in out and out[field]:
			if "mail" in field:
				out[field] = mask_email(out[field])
			else:
				out[field] = mask_mobile(str(out[field]))
	return out
