# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare activity — replace Customer terminology with Patient everywhere in UX."""

from __future__ import annotations

import frappe

HEALTHCARE_HIDDEN_DOCTYPES = (
	"Customer",
	"Customer Profile",
	"CRM Lead",
	"CRM Opportunity",
	"CRM Case Ticket",
	"CRM Interaction Log",
)

# English source strings → patient-first labels (Frappe __ translation keys).
PATIENT_TERMINOLOGY_EN: dict[str, str] = {
	"Customer": "Patient",
	"Customers": "Patients",
	"customer": "patient",
	"customers": "patients",
	"New Customer": "New Patient",
	"Create Customer": "Create Patient",
	"Customer Name": "Patient Name",
	"Customer name": "Patient name",
	"Billing customer": "Patient",
	"Billing Customer": "Patient",
	"Billing account (ERP)": "Patient billing (internal)",
	"Select Customer": "Select Patient",
	"Customer Profile": "Patient Record",
	"Customer Receipt": "Patient Receipt",
	"Customer Group": "Patient Group",
	"Linked Accounting Customer": "Patient billing account",
	"Customer Type": "Patient Type",
	"Customer Email": "Patient Email",
	"Customer and Payment": "Patient and Payment",
	"Customer 360": "Patient 360",
	"CRM Customer Revenue": "Patient Revenue",
	"Add Customer": "Add Patient",
	"Default Customer": "Default Patient",
	"Primary Customer": "Primary Patient",
	"End Customer": "Patient",
	"Walk-in Customer": "Walk-in Patient",
}

PATIENT_TERMINOLOGY_AR: dict[str, str] = {
	"Customer": "مريض",
	"Customers": "مرضى",
	"customer": "مريض",
	"customers": "مرضى",
	"New Customer": "مريض جديد",
	"Create Customer": "إنشاء مريض",
	"Customer Name": "اسم المريض",
	"Customer name": "اسم المريض",
	"Billing customer": "مريض",
	"Billing Customer": "مريض",
	"Billing account (ERP)": "فوترة المريض (داخلي)",
	"Select Customer": "اختر مريضاً",
	"Customer Profile": "ملف المريض",
	"Customer Receipt": "قبض من مريض",
	"Customer Group": "مجموعة مرضى",
	"Linked Accounting Customer": "حساب فوترة المريض",
	"Customer Type": "نوع المريض",
	"Customer Email": "بريد المريض",
	"Customer and Payment": "المريض والدفع",
	"Customer 360": "مريض 360",
	"CRM Customer Revenue": "إيرادات المرضى",
	"Add Customer": "إضافة مريض",
	"Default Customer": "المريض الافتراضي",
	"Primary Customer": "المريض الرئيسي",
	"End Customer": "مريض",
	"Walk-in Customer": "مريض زائر",
	"Patient": "مريض",
	"Patients": "مرضى",
	"Healthcare Patient": "مريض",
}


def is_healthcare_activity(activity: str | None = None) -> bool:
	if activity is not None:
		return _norm(activity) == "Healthcare"
	try:
		from omnexa_core.omnexa_core.app_visibility import get_user_company_activity

		if get_user_company_activity() == "Healthcare":
			return True
	except Exception:
		pass
	branch = frappe.defaults.get_user_default("Branch")
	if branch and frappe.db.exists("Branch", branch):
		if (frappe.db.get_value("Branch", branch, "branch_demo_activity") or "").strip() == "Healthcare":
			return True
	return False


def _norm(activity: str) -> str:
	return (activity or "").strip().split("(")[0].strip() or "General"


def get_patient_terminology_messages(lang: str | None = None) -> dict[str, str]:
	lang = (lang or frappe.local.lang or "en").lower()
	base = dict(PATIENT_TERMINOLOGY_EN)
	if lang.startswith("ar"):
		base.update(PATIENT_TERMINOLOGY_AR)
	return base


def apply_boot_terminology(bootinfo) -> None:
	if not is_healthcare_activity():
		return

	lang = bootinfo.get("lang") or frappe.local.lang or "en"
	terms = get_patient_terminology_messages(lang)
	bootinfo.omnexa_healthcare_mode = True
	bootinfo.omnexa_patient_terminology = terms
	existing = list(bootinfo.get("omnexa_hidden_doctypes") or [])
	bootinfo.omnexa_hidden_doctypes = sorted(set(existing) | set(HEALTHCARE_HIDDEN_DOCTYPES))

	messages = bootinfo.get("__messages") or {}
	if isinstance(messages, dict):
		messages = dict(messages)
		messages.update(terms)
		try:
			from omnexa_healthcare.i18n.healthcare_i18n_catalog import build_desk_messages

			messages.update(build_desk_messages(lang))
		except Exception:
			pass
		bootinfo["__messages"] = messages
