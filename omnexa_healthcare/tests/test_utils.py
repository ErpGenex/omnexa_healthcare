# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def ensure_currency_and_country():
	if not frappe.db.exists("Currency", "EGP"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1}).insert(
			ignore_permissions=True
		)
	if not frappe.db.exists("Country", "Egypt"):
		frappe.get_doc({"doctype": "Country", "country_name": "Egypt", "code": "EG"}).insert(ignore_permissions=True)


def setup_admin_all_branch_access(user: str | None = None):
	"""Allow Administrator to create healthcare docs in any branch during tests."""
	user = user or frappe.session.user
	frappe.set_user(user)
	frappe.defaults.set_user_default("omnexa_view_all_branches", "1", user)
	frappe.defaults.set_user_default("omnexa_view_branch", "__ALL__", user)


def make_test_branch(company: str, code: str) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Branch",
			"company": company,
			"branch_name": f"Branch {code}",
			"branch_code": code,
			"status": "Active",
			"eta_usb_signing_pin": "0000",
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_company_stock_gl(company: str, warehouse: str | None = None) -> None:
	"""Minimal GL mapping so Material Issue stock entries pass omnexa_accounting validation."""
	if not frappe.db.exists("DocType", "GL Account"):
		return

	def _gl(number: str, name: str, account_class: str = "Expense") -> str:
		existing = frappe.db.get_value("GL Account", {"company": company, "account_number": number}, "name")
		if existing:
			return existing
		doc = frappe.new_doc("GL Account")
		doc.company = company
		doc.account_number = number
		doc.account_name = name
		doc.account_class = account_class
		doc.account_type = account_class
		doc.is_group = 0
		doc.insert(ignore_permissions=True)
		return doc.name

	inv = _gl("1104", "Inventory Test", "Asset")
	cogs = _gl("5101", "COGS Test", "Expense")
	opex = _gl("5102", "OPEX Test", "Expense")
	updates = {"default_inventory_gl": inv, "default_cogs_gl": cogs, "default_opex_gl": opex}
	if frappe.get_meta("Company").has_field("default_inventory_gl"):
		frappe.db.set_value("Company", company, updates, update_modified=False)
	if warehouse and frappe.get_meta("Warehouse").has_field("inventory_gl_account"):
		frappe.db.set_value("Warehouse", warehouse, "inventory_gl_account", inv, update_modified=False)
