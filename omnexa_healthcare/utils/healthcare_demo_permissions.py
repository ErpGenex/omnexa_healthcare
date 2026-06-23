# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Demo role permissions — Page read + journey page roles + healthcare DocTypes."""

from __future__ import annotations

import frappe

from omnexa_healthcare.api.healthcare_role_demo import ROLE_SPECS

BASE_ROLES = ("Desk User", "System Manager", "Company Admin")

# Page name -> role-specific access (plus BASE_ROLES)
JOURNEY_PAGE_ROLES: dict[str, tuple[str, ...]] = {
	"healthcare-reception-desk": ("Healthcare Receptionist",),
	"healthcare-cashier-desk": ("Healthcare Cashier",),
	"healthcare-physician-workbench": ("Healthcare Physician",),
	"healthcare-patient-consumer": ("Healthcare Patient Portal",),
	"healthcare-nursing-portal": ("Healthcare Nurse",),
	"healthcare-pharmacy-desk": ("Healthcare Pharmacist",),
	"healthcare-executive-dashboard": ("Healthcare Manager", "Healthcare Executive"),
	"healthcare-finance-desk": ("Healthcare CFO",),
	"healthcare-patient-queue": (
		"Healthcare Receptionist",
		"Healthcare Nurse",
		"Healthcare Physician",
	),
	"healthcare-patient-chart": ("Healthcare Physician",),
	"healthcare-erx-writer": ("Healthcare Physician",),
	"healthcare-device-admin": ("System Manager", "Company Admin"),
	"healthcare-workcenter": ("System Manager",),
	"healthcare-lab-workbench": ("Healthcare Physician", "Healthcare Nurse"),
	"healthcare-radiology-worklist": ("Healthcare Physician", "Healthcare Nurse"),
	"healthcare-dicom-viewer": ("Healthcare Physician",),
	"healthcare-er-board": ("Healthcare Physician", "Healthcare Nurse"),
	"healthcare-icu-board": ("Healthcare Nurse",),
	"healthcare-bed-map": ("Healthcare Nurse",),
	"healthcare-ot-board": ("Healthcare Physician",),
	"healthcare-dialysis-desk": ("Healthcare Nurse",),
	"healthcare-ld-board": ("Healthcare Nurse",),
	"healthcare-optometry-desk": ("Healthcare Physician",),
	"healthcare-dental-chart": ("Healthcare Physician",),
	"healthcare-rehab-desk": ("Healthcare Nurse",),
	"healthcare-diet-desk": ("Healthcare Nurse",),
	"healthcare-blood-desk": ("Healthcare Nurse",),
	"healthcare-morgue-desk": ("Healthcare Nurse",),
	"healthcare-telehealth-room": ("Healthcare Physician",),
	"healthcare-appointment-calendar": ("Healthcare Receptionist",),
	"healthcare-practitioner-roster": ("Healthcare Executive",),
	"healthcare-pharmacy-rx-verify": ("Healthcare Pharmacist",),
	"healthcare-appointments-desk": ("Healthcare Receptionist",),
	"healthcare-patients-desk": ("Healthcare Receptionist",),
}

# Role -> DocTypes granted read/write/create for desk workflows
ROLE_DOCTYPE_PERMS: dict[str, list[dict]] = {
	"Healthcare Receptionist": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 1, "create": 1, "select": 1},
	],
	"Healthcare Cashier": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 1, "create": 0, "select": 1},
	],
	"Healthcare Physician": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 1, "create": 1, "select": 1},
	],
	"Healthcare Patient Portal": [
		{"read": 1, "write": 0, "create": 0, "select": 1},
	],
	"Healthcare Nurse": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 0, "create": 0, "select": 1},
		{"read": 1, "write": 1, "create": 1, "select": 1},
	],
	"Healthcare Manager": [
		{"read": 1, "write": 0, "create": 0, "select": 1},
		{"read": 1, "write": 0, "create": 0, "select": 1},
	],
	"Healthcare Pharmacist": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 0, "create": 0, "select": 1},
	],
	"Healthcare CFO": [
		{"read": 1, "write": 1, "create": 1, "select": 1},
		{"read": 1, "write": 0, "create": 0, "select": 1},
	],
	"Healthcare Executive": [
		{"read": 1, "write": 0, "create": 0, "select": 1},
		{"read": 1, "write": 0, "create": 0, "select": 1},
	],
}

ROLE_DOCTYPE_NAMES: dict[str, list[str]] = {
	"Healthcare Receptionist": ["Healthcare Patient", "Healthcare Appointment"],
	"Healthcare Cashier": ["Healthcare Service Charge", "Healthcare Appointment"],
	"Healthcare Physician": [
		"Healthcare Encounter",
		"Healthcare Service Request",
		"Healthcare Medication Statement",
	],
	"Healthcare Patient Portal": ["Healthcare Appointment"],
	"Healthcare Nurse": [
		"Healthcare Appointment",
		"Healthcare Observation",
		"Healthcare Medication Administration Record",
		"Healthcare Morgue Case",
	],
	"Healthcare Manager": ["Healthcare Appointment", "Healthcare Patient"],
	"Healthcare Pharmacist": [
		"Healthcare Medication Dispense",
		"Healthcare Medication Statement",
		"Healthcare Patient",
	],
	"Healthcare CFO": ["Healthcare Service Charge", "Healthcare Appointment"],
	"Healthcare Executive": ["Healthcare Appointment", "Healthcare Patient"],
}


def _all_demo_roles() -> list[str]:
	roles = list(BASE_ROLES)
	for spec in ROLE_SPECS:
		if spec["role"] not in roles:
			roles.append(spec["role"])
	return roles


def _ensure_custom_docperm(doctype: str, role: str, perms: dict) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	existing = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Custom DocPerm", existing)
		for key, val in perms.items():
			setattr(doc, key, val)
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"permlevel": 0,
			**perms,
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_page_doctype_read() -> None:
	for role in _all_demo_roles():
		_ensure_custom_docperm(
			"Page",
			role,
			{"read": 1, "write": 0, "create": 0, "select": 1, "export": 0, "print": 0, "email": 0, "share": 0},
		)


def _ensure_page_has_roles(page_name: str, roles: tuple[str, ...]) -> None:
	if not frappe.db.exists("Page", page_name):
		return
	existing = set(
		frappe.get_all("Has Role", filters={"parent": page_name, "parenttype": "Page"}, pluck="role")
	)
	target = set(BASE_ROLES) | set(roles)
	for role in sorted(target):
		if role in existing or not frappe.db.exists("Role", role):
			continue
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": page_name,
				"parenttype": "Page",
				"parentfield": "roles",
				"role": role,
			}
		).insert(ignore_permissions=True)


def _ensure_role_doctype_perms() -> None:
	for role, doctypes in ROLE_DOCTYPE_NAMES.items():
		perm_templates = ROLE_DOCTYPE_PERMS.get(role, [{"read": 1, "select": 1}])
		for idx, dt in enumerate(doctypes):
			if not frappe.db.exists("DocType", dt):
				continue
			perms = perm_templates[idx] if idx < len(perm_templates) else perm_templates[-1]
			full = {
				"read": 0,
				"write": 0,
				"create": 0,
				"delete": 0,
				"submit": 0,
				"cancel": 0,
				"amend": 0,
				"select": 0,
				"export": 0,
				"print": 0,
				"email": 0,
				"report": 1,
				"share": 0,
			}
			full.update(perms)
			_ensure_custom_docperm(dt, role, full)


def _collect_pages_from_specs() -> dict[str, set[str]]:
	mapping: dict[str, set[str]] = {}
	for spec in ROLE_SPECS:
		role = spec["role"]
		for _sec, items in spec.get("sections", []):
			for link_type, link_to, _lbl in items:
				if link_type != "Page":
					continue
				mapping.setdefault(link_to, set()).add(role)
	return mapping


def sync_healthcare_demo_permissions() -> dict:
	"""Grant Page read + journey page roles + healthcare DocType access for demo users."""
	_ensure_page_doctype_read()
	_ensure_role_doctype_perms()

	pages_synced = []
	spec_pages = _collect_pages_from_specs()
	all_page_keys = set(JOURNEY_PAGE_ROLES) | set(spec_pages)
	for page_name in sorted(all_page_keys):
		roles = tuple(JOURNEY_PAGE_ROLES.get(page_name, ()))
		roles_set = set(roles) | spec_pages.get(page_name, set())
		_ensure_page_has_roles(page_name, tuple(sorted(roles_set)))
		pages_synced.append(page_name)

	frappe.clear_cache(doctype="Page")
	frappe.clear_cache(doctype="DocType")
	return {"ok": True, "pages": pages_synced, "roles": _all_demo_roles()}
