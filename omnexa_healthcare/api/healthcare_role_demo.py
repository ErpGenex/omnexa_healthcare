# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare role-based luxury workspaces + demo login users."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.vertical_workspace_sync import build_content_from_link_rows

DEMO_PASSWORD = "Healthcare@Demo2026"

ROLE_SPECS: list[dict] = [
	{
		"role": "Healthcare Receptionist",
		"workspace": "Healthcare Reception",
		"title": "🏥 Reception Command",
		"default_route": "/app/healthcare-reception-desk",
		"email": "reception@demo.health",
		"first_name": "Sara",
		"last_name": "Reception",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-reception-desk", "Reception Desk"),
				("Page", "healthcare-patient-queue", "Smart Queue"),
			]),
			("📋 Patients", [
				("DocType", "Healthcare Patient", "Patients"),
				("DocType", "Healthcare Appointment", "Appointments"),
			]),
		],
	},
	{
		"role": "Healthcare Cashier",
		"workspace": "Healthcare Cashier",
		"title": "💰 Treasury Desk",
		"default_route": "/app/healthcare-cashier-desk",
		"email": "cashier@demo.health",
		"first_name": "Ahmed",
		"last_name": "Cashier",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-cashier-desk", "Cashier Desk"),
			]),
			("💳 Billing", [
				("DocType", "Healthcare Service Charge", "Service Charges"),
				("DocType", "Healthcare Appointment", "Appointments"),
			]),
		],
	},
	{
		"role": "Healthcare Physician",
		"workspace": "Healthcare Physician",
		"title": "👨‍⚕️ Physician Excellence",
		"default_route": "/app/healthcare-physician-workbench",
		"email": "physician@demo.health",
		"first_name": "Dr. Omar",
		"last_name": "Hassan",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-physician-workbench", "Physician Workbench"),
				("Page", "healthcare-erx-writer", "ePrescription"),
				("Page", "healthcare-patient-chart", "Medical File"),
			]),
			("🩺 Clinical", [
				("DocType", "Healthcare Encounter", "Encounters"),
				("DocType", "Healthcare Service Request", "Orders"),
			]),
		],
	},
	{
		"role": "Healthcare Patient Portal",
		"workspace": "Healthcare Patient Portal",
		"title": "👤 My Health Journey",
		"default_route": "/app/healthcare-patient-consumer",
		"email": "patient@demo.health",
		"first_name": "Mona",
		"last_name": "Patient",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-patient-consumer", "Book · Pay · Track"),
			]),
		],
	},
	{
		"role": "Healthcare Nurse",
		"workspace": "Healthcare Nursing",
		"title": "🩹 Nursing Station",
		"default_route": "/app/healthcare-nursing-portal",
		"email": "nurse@demo.health",
		"first_name": "Nadia",
		"last_name": "Nurse",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-nursing-portal", "Nursing Portal"),
				("Page", "healthcare-patient-queue", "Queue Board"),
			]),
			("📊 Vitals", [
				("DocType", "Healthcare Observation", "Observations"),
			]),
		],
	},
	{
		"role": "Healthcare Executive",
		"workspace": "Healthcare Executive",
		"title": "📊 Executive Intelligence",
		"default_route": "/app/healthcare-executive-dashboard",
		"email": "executive@demo.health",
		"first_name": "Karim",
		"last_name": "Executive",
		"sections": [
			("📊 Analytics", [
				("Page", "healthcare-executive-dashboard", "Executive Dashboard"),
				("Page", "healthcare-demo-hub", "Demo Hub"),
			]),
		],
	},
	{
		"role": "Healthcare Pharmacist",
		"workspace": "Healthcare Pharmacy",
		"title": "💊 Pharmacy Desk",
		"default_route": "/app/healthcare-pharmacy-desk",
		"email": "pharmacist@demo.health",
		"first_name": "Layla",
		"last_name": "Pharmacist",
		"sections": [
			("✨ Omnexa Journey", [
				("Page", "healthcare-pharmacy-desk", "Pharmacy Desk"),
				("Page", "healthcare-pharmacy-rx-verify", "Rx Verify"),
			]),
		],
	},
	{
		"role": "Healthcare CFO",
		"workspace": "Healthcare Finance",
		"title": "💼 Finance Desk",
		"default_route": "/app/healthcare-finance-desk",
		"email": "cfo@demo.health",
		"first_name": "Hana",
		"last_name": "Finance",
		"sections": [
			("💼 Finance", [
				("Page", "healthcare-finance-desk", "Finance Desk"),
				("Page", "healthcare-cashier-desk", "Cashier Desk"),
			]),
		],
	},
	{
		"role": "Healthcare Manager",
		"workspace": "Healthcare Manager",
		"title": "📊 Hospital Manager",
		"default_route": "/app/healthcare-executive-dashboard",
		"email": "manager@demo.health",
		"first_name": "Karim",
		"last_name": "Manager",
		"sections": [
			("📊 Management", [
				("Page", "healthcare-executive-dashboard", "Executive Dashboard"),
				("Page", "healthcare-demo-hub", "Demo Hub"),
			]),
		],
	},
]

HEALTHCARE_MODULES = frozenset({"Omnexa Healthcare", "Healthcare"})


def _ensure_role(role_name: str) -> None:
	if not frappe.db.exists("Role", role_name):
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _exists_link(link_type: str, link_to: str) -> bool:
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	return False


def _build_rows(sections: list) -> list[dict]:
	rows: list[dict] = []
	for label, items in sections:
		valid = [(t, to, lbl) for t, to, lbl in items if _exists_link(t, to)]
		if not valid:
			continue
		rows.append({"label": label, "type": "Card Break", "link_type": "DocType"})
		for link_type, link_to, lbl in valid:
			row = {"type": "Link", "label": lbl, "link_type": link_type, "link_to": link_to}
			if link_type == "Report":
				row["is_query_report"] = 1
			rows.append(row)
	return rows


def sync_role_workspace(spec: dict) -> str:
	role = spec["role"]
	ws_name = spec["workspace"]
	_ensure_role(role)
	rows = _build_rows(spec["sections"])
	if not frappe.db.exists("Workspace", ws_name):
		ws = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": ws_name,
				"title": ws_name,
				"module": "Omnexa Healthcare",
				"public": 0,
				"for_user": "",
				"content": "[]",
				"sequence_id": 2.0,
			}
		)
		ws.insert(ignore_permissions=True)
	else:
		ws = frappe.get_doc("Workspace", ws_name)

	ws.set("links", [])
	for row in rows:
		ws.append("links", row)
	ws.set("roles", [{"role": role}])
	ws.title = spec.get("title") or ws_name
	ws.content = build_content_from_link_rows(rows, ws, title=ws.title, slug=frappe.scrub(ws_name))
	ws.flags.ignore_permissions = True
	ws.save()
	return ws.name


def _block_non_healthcare_modules(user_doc) -> None:
	all_modules = frappe.get_all("Module Def", pluck="name")
	blocked = [m for m in all_modules if m not in HEALTHCARE_MODULES and m not in ("Core", "Desk", "Integrations")]
	user_doc.set("block_modules", [{"module": m} for m in blocked[:40]])


def _ensure_demo_user(spec: dict, company: str, branch: str) -> str:
	email = spec["email"]
	role = spec["role"]
	ws = spec["workspace"]
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": spec["first_name"],
				"last_name": spec["last_name"],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user.enabled = 1
	user.new_password = DEMO_PASSWORD
	if not user.roles or not any(r.role == role for r in user.roles):
		user.append("roles", {"role": role})
	_block_non_healthcare_modules(user)
	user.default_workspace = ws
	user.save(ignore_permissions=True)
	frappe.defaults.set_user_default("Company", company, email)
	frappe.defaults.set_user_default("Branch", branch, email)
	return email


@frappe.whitelist()
def seed_full_healthcare_demo(company: str | None = None, branch: str | None = None, patients: int = 50) -> dict:
	"""Seed hospital demo data + role workspaces + demo users."""
	frappe.only_for("System Manager")
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	if not company or not branch:
		frappe.throw(_("Company and Branch are required."))
	from omnexa_healthcare.utils.branch_demo_seed import seed_healthcare_hospital_demo

	hospital = seed_healthcare_hospital_demo(company, branch, patients=int(patients), force=1, include_financial=1)
	roles = seed_healthcare_role_demo(company=company, branch=branch)
	return {"hospital": hospital, **roles}


@frappe.whitelist()
def seed_healthcare_role_demo(company: str | None = None, branch: str | None = None) -> dict:
	"""Create role workspaces + demo users (System Manager)."""
	frappe.only_for("System Manager")
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	if not company or not branch:
		frappe.throw(_("Set Company and Branch defaults first, or seed hospital demo."))

	workspaces = []
	users = []
	for spec in ROLE_SPECS:
		workspaces.append(sync_role_workspace(spec))
		users.append(_ensure_demo_user(spec, company, branch))

	frappe.db.commit()
	return {
		"ok": True,
		"password": DEMO_PASSWORD,
		"workspaces": workspaces,
		"users": get_healthcare_demo_credentials()["users"],
		"message": _("Healthcare role demo ready. Each user sees only their workspace."),
	}


@frappe.whitelist()
def get_healthcare_demo_credentials() -> dict:
	frappe.only_for("System Manager")
	return {
		"password": DEMO_PASSWORD,
		"users": [
			{
				"role": s["role"],
				"email": s["email"],
				"workspace": s["workspace"],
				"route": s["default_route"],
				"name": f"{s['first_name']} {s['last_name']}",
			}
			for s in ROLE_SPECS
		],
	}
