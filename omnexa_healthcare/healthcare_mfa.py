# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""MFA enforcement for PHI-access clinical roles."""

from __future__ import annotations

import frappe

PHI_ROLES = ("Physician", "Nursing User", "Company Admin", "System Manager")


def apply_mfa_boot_policy(bootinfo) -> None:
	try:
		settings = frappe.get_cached_doc("Healthcare Settings")
	except Exception:
		return
	if not settings.get("enforce_mfa_for_phi_roles"):
		return
	bootinfo.omnexa_healthcare_mfa_required = True
	bootinfo.omnexa_healthcare_phi_roles = list(PHI_ROLES)


def validate_phi_role_mfa(user: str | None = None) -> None:
	"""Called on session — warn if clinical user lacks 2FA when enforcement enabled."""
	try:
		settings = frappe.get_cached_doc("Healthcare Settings")
	except Exception:
		return
	if not settings.get("enforce_mfa_for_phi_roles"):
		return
	user = user or frappe.session.user
	if user == "Guest":
		return
	roles = set(frappe.get_roles(user))
	if not roles.intersection(PHI_ROLES):
		return
	if not frappe.db.get_value("User", user, "enable_two_factor_auth"):
		frappe.msgprint(
			frappe._("Two-factor authentication is required for healthcare PHI access. Please enable 2FA in your profile."),
			indicator="orange",
			title=frappe._("Healthcare Security"),
		)
