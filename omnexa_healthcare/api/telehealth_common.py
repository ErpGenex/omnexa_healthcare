# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.utils import cstr


def get_jitsi_server() -> str:
	return cstr(frappe.db.get_single_value("Healthcare Settings", "jitsi_server_url")) or "https://meet.jit.si"


def build_jitsi_join_url(room_id: str, display_name: str | None = None) -> str:
	base = get_jitsi_server().rstrip("/")
	url = f"{base}/{room_id}"
	if display_name:
		from urllib.parse import quote

		url = f"{url}#userInfo.displayName={quote(display_name)}"
	return url
