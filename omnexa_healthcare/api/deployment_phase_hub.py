# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Healthcare Demo Hub — deployment phase control panels (clinic / hospital / national)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from omnexa_healthcare.api.portal_catalog import PORTAL_CATALOG

PHASE_CACHE_KEY = "healthcare_demo_deployment_phase"

CLINIC_PORTAL_IDS = frozenset(
	{
		"reception",
		"cashier",
		"physician",
		"patient",
		"queue",
		"appointment",
		"patients",
		"pharmacy",
		"rx-verify",
		"erx",
		"chart",
		"calendar",
		"telehealth",
	}
)

HOSPITAL_PORTAL_IDS = frozenset(p["id"] for p in PORTAL_CATALOG if p["id"] not in ("demo-hub",))

NATIONAL_EXTRA_PORTAL_IDS = frozenset({"executive", "finance", "roster", "device-admin"})

PHASE_DEFINITIONS: list[dict] = [
	{
		"id": "clinic",
		"icon": "🩺",
		"label_ar": "المرحلة 1 — عيادة خاصة",
		"label_en": "Phase 1 — Private Clinic",
		"summary_ar": "فرع واحد · OPD · استقبال · طبيب · صيدلية · حجز ويب",
		"summary_en": "Single branch · OPD · reception · physician · pharmacy · web booking",
		"company_abbr": "CLN",
		"company_name": "عيادة النور الطبية",
		"branch_code": "HO",
		"branch_name": "المقر الرئيسي",
		"site_slug": "clinic-nour",
		"portal_ids": sorted(CLINIC_PORTAL_IDS),
		"seed_patients": 12,
	},
	{
		"id": "hospital",
		"icon": "🏥",
		"label_ar": "المرحلة 2 — مستشفى متعدد التخصصات",
		"label_en": "Phase 2 — Multi-Specialty Hospital",
		"summary_ar": "جميع التخصصات · IPD · طوارئ · مختبر · أشعة · RCM · 35+ بوابة",
		"summary_en": "All specialties · IPD · ER · lab · radiology · RCM · 35+ portals",
		"company_abbr": "MH",
		"company_name": "مستشفى الحياة",
		"branch_code": "HO",
		"branch_name": "المقر الرئيسي",
		"site_slug": "mh-ho",
		"portal_ids": sorted(HOSPITAL_PORTAL_IDS),
		"seed_patients": 50,
	},
	{
		"id": "national",
		"icon": "🌍",
		"label_ar": "المرحلة 3 — شبكة وطنية",
		"label_en": "Phase 3 — National Network",
		"summary_ar": "محافظات · عدة مستشفيات · فروع متعددة · تقارير مجمّعة",
		"summary_en": "Governorates · multiple hospitals · branches · consolidated reporting",
		"company_abbr": "MH-EG",
		"company_name": "الهيئة الوطنية للرعاية الصحية",
		"branch_code": "HO",
		"branch_name": "المقر المركزي",
		"site_slug": "mh-eg",
		"portal_ids": sorted(HOSPITAL_PORTAL_IDS | NATIONAL_EXTRA_PORTAL_IDS),
		"seed_patients": 0,
	},
]

NATIONAL_GOVERNORATES: list[dict] = [
	{
		"abbr": "MH-CAI",
		"name_ar": "محافظة القاهرة",
		"name_en": "Cairo Governorate",
		"branches": [
			{
				"code": "TG-HO",
				"name_ar": "مستشفى الحياة — التجمع",
				"facility": "Hospital",
				"site_slug": "mh-cai-tg",
				"seed_mode": "hospital",
				"patients": 15,
			},
			{
				"code": "NSR",
				"name_ar": "عيادة خارجية — مدينة نصر",
				"facility": "Clinic",
				"site_slug": "mh-cai-nsr",
				"seed_mode": "clinic",
				"patients": 8,
			},
			{
				"code": "MAD",
				"name_ar": "عيادة خارجية — المعادي",
				"facility": "Clinic",
				"site_slug": "mh-cai-mad",
				"seed_mode": "clinic",
				"patients": 8,
			},
		],
	},
	{
		"abbr": "MH-ALX",
		"name_ar": "محافظة الإسكندرية",
		"name_en": "Alexandria Governorate",
		"branches": [
			{
				"code": "HO",
				"name_ar": "مستشفى الحياة — سموحة",
				"facility": "Hospital",
				"site_slug": "mh-alx-ho",
				"seed_mode": "hospital",
				"patients": 12,
			},
			{
				"code": "BA",
				"name_ar": "فرع برج العرب",
				"facility": "Clinic",
				"site_slug": "mh-alx-ba",
				"seed_mode": "clinic",
				"patients": 6,
			},
		],
	},
	{
		"abbr": "MH-DLT",
		"name_ar": "محافظة الدلتا",
		"name_en": "Delta Governorate",
		"branches": [
			{
				"code": "HO",
				"name_ar": "مستشفى المنصورة",
				"facility": "Hospital",
				"site_slug": "mh-dlt-ho",
				"seed_mode": "hospital",
				"patients": 10,
			},
			{
				"code": "TAN",
				"name_ar": "فرع طنطا",
				"facility": "Clinic",
				"site_slug": "mh-dlt-tan",
				"seed_mode": "clinic",
				"patients": 6,
			},
		],
	},
]


def _phase_by_id(phase_id: str) -> dict:
	for row in PHASE_DEFINITIONS:
		if row["id"] == phase_id:
			return row
	frappe.throw(_("Unknown deployment phase: {0}").format(phase_id))


def _ensure_pilot_geo() -> None:
	if not frappe.db.exists("Currency", "EGP"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1}).insert(
			ignore_permissions=True
		)
	if not frappe.db.exists("Country", "Egypt"):
		frappe.get_doc({"doctype": "Country", "country_name": "Egypt", "code": "EG"}).insert(
			ignore_permissions=True
		)


def _ensure_company(abbr: str, company_name: str) -> str:
	_ensure_pilot_geo()
	if frappe.db.exists("Company", abbr):
		return abbr
	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": company_name,
			"abbr": abbr,
			"default_currency": "EGP",
			"country": "Egypt",
			"status": "Active",
		}
	)
	doc.insert(ignore_permissions=True)
	if frappe.get_meta("Company").has_field("enable_branches"):
		frappe.db.set_value("Company", abbr, "enable_branches", 1, update_modified=False)
	return abbr


def _ensure_branch(company: str, branch_code: str, branch_name: str, *, is_head_office: int = 0) -> str:
	branch_name_doc = f"{company}-{branch_code}"
	if frappe.db.exists("Branch", branch_name_doc):
		if is_head_office:
			frappe.db.set_value("Branch", branch_name_doc, "is_head_office", 1, update_modified=False)
		return branch_name_doc

	if is_head_office and frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name"):
		is_head_office = 0

	doc = frappe.get_doc(
		{
			"doctype": "Branch",
			"branch_name": branch_name,
			"branch_code": branch_code,
			"company": company,
			"status": "Active",
			"is_head_office": cint(is_head_office),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_branch_website(branch: str, company: str, site_slug: str, name_ar: str, name_en: str) -> None:
	if frappe.db.exists("Healthcare Branch Website", branch):
		frappe.db.set_value(
			"Healthcare Branch Website",
			branch,
			{
				"is_enabled": 1,
				"site_slug": site_slug,
				"hospital_name_ar": name_ar,
				"hospital_name_en": name_en,
			},
			update_modified=True,
		)
		return
	frappe.get_doc(
		{
			"doctype": "Healthcare Branch Website",
			"branch": branch,
			"company": company,
			"is_enabled": 1,
			"site_slug": site_slug,
			"hospital_name_ar": name_ar,
			"hospital_name_en": name_en,
		}
	).insert(ignore_permissions=True)


def _set_active_phase(phase_id: str, company: str, branch: str) -> None:
	frappe.cache().set_value(PHASE_CACHE_KEY, phase_id)
	frappe.defaults.set_user_default("Company", company)
	frappe.defaults.set_user_default("Branch", branch)
	try:
		settings = frappe.get_single("Healthcare Settings")
		settings.public_website_default_branch = branch
		settings.enable_patient_otp = 0 if phase_id == "clinic" else settings.enable_patient_otp
		settings.allow_cross_branch_appointments = 1 if phase_id == "national" else settings.allow_cross_branch_appointments
		settings.allow_cross_branch_patient_access = 1 if phase_id == "national" else settings.allow_cross_branch_patient_access
		settings.flags.ignore_permissions = True
		settings.save()
	except Exception:
		pass


def _branch_stats(company: str, branch: str) -> dict:
	return {
		"departments": frappe.db.count("Healthcare Department", {"company": company, "branch": branch}),
		"practitioners": frappe.db.count("Healthcare Practitioner", {"company": company}),
		"patients": frappe.db.count("Healthcare Patient", {"company": company, "branch": branch}),
		"beds": frappe.db.count("Healthcare Bed", {"company": company, "branch": branch}),
		"appointments_today": frappe.db.count(
			"Healthcare Appointment",
			{"company": company, "branch": branch, "appointment_date": [">=", frappe.utils.today()]},
		),
	}


def _portal_rows(portal_ids: set[str] | frozenset[str]) -> list[dict]:
	rows = []
	for p in PORTAL_CATALOG:
		if p["id"] not in portal_ids:
			continue
		rows.append(
			{
				**p,
				"exists": bool(frappe.db.exists("Page", p["page"])),
			}
		)
	return rows


def _resolve_company_branch(phase: dict) -> tuple[str, str]:
	company = phase["company_abbr"]
	if not frappe.db.exists("Company", company):
		if phase["id"] == "hospital" and frappe.db.exists("Company", "MH"):
			company = "MH"
	branch = f"{company}-{phase['branch_code']}"
	if not frappe.db.exists("Branch", branch):
		alt = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
		if alt:
			branch = alt
	return company, branch


def _national_network_status() -> dict:
	governorates = []
	total_branches = 0
	seeded_branches = 0
	for gov in NATIONAL_GOVERNORATES:
		branches = []
		for spec in gov["branches"]:
			branch_name = f"{gov['abbr']}-{spec['code']}"
			exists = bool(frappe.db.exists("Branch", branch_name))
			facility_type = spec["facility"]
			seeded = (
				bool(
					frappe.db.exists(
						"Healthcare Facility Profile",
						{"company": gov["abbr"], "branch": branch_name, "facility_type": facility_type},
					)
				)
				if exists
				else False
			)
			if exists:
				total_branches += 1
				if seeded:
					seeded_branches += 1
			branches.append(
				{
					"branch": branch_name,
					"name_ar": spec["name_ar"],
					"facility": spec["facility"],
					"site_slug": spec["site_slug"],
					"exists": exists,
					"seeded": seeded,
					"booking_url": f"/hospital/booking?site={spec['site_slug']}",
					"site_url": f"/hospital?site={spec['site_slug']}",
				}
			)
		governorates.append(
			{
				"company": gov["abbr"],
				"label_ar": gov["name_ar"],
				"label_en": gov["name_en"],
				"exists": bool(frappe.db.exists("Company", gov["abbr"])),
				"branches": branches,
			}
		)
	return {
		"governorates": governorates,
		"governorate_count": len(governorates),
		"branch_count": total_branches,
		"seeded_branch_count": seeded_branches,
	}


@frappe.whitelist()
def get_deployment_phases_dashboard() -> dict:
	"""Return phase control panels for Healthcare Demo Hub."""
	frappe.only_for("System Manager")
	active_phase = frappe.cache().get_value(PHASE_CACHE_KEY) or ""
	default_company = frappe.defaults.get_user_default("Company") or ""
	default_branch = frappe.defaults.get_user_default("Branch") or ""

	phases = []
	for phase in PHASE_DEFINITIONS:
		company, branch = _resolve_company_branch(phase)
		ready = bool(frappe.db.exists("Company", company) and frappe.db.exists("Branch", branch))
		stats = _branch_stats(company, branch) if ready else {}
		portals = _portal_rows(set(phase["portal_ids"]))
		item = {
			**phase,
			"company": company,
			"branch": branch,
			"ready": ready,
			"active": active_phase == phase["id"],
			"stats": stats,
			"portals": portals,
			"portal_count": len(portals),
			"booking_url": f"/hospital/booking?site={phase['site_slug']}",
			"site_url": f"/hospital?site={phase['site_slug']}",
		}
		if phase["id"] == "national":
			item["network"] = _national_network_status()
		phases.append(item)

	return {
		"ok": True,
		"active_phase": active_phase,
		"default_company": default_company,
		"default_branch": default_branch,
		"phases": phases,
	}


def _seed_branch(company: str, branch: str, *, mode: str, patients: int, force: int = 1) -> dict:
	from omnexa_healthcare.utils.branch_demo_seed import seed_healthcare_clinic_demo, seed_healthcare_hospital_demo

	if mode == "clinic":
		return seed_healthcare_clinic_demo(company, branch, patients=patients, force=force, include_financial=1)
	return seed_healthcare_hospital_demo(company, branch, patients=patients, force=force, include_financial=1)


def _activate_clinic_phase(phase: dict, force: int) -> dict:
	company = _ensure_company(phase["company_abbr"], phase["company_name"])
	branch = _ensure_branch(company, phase["branch_code"], phase["branch_name"], is_head_office=1)
	_ensure_branch_website(
		branch,
		company,
		phase["site_slug"],
		"عيادة النور الطبية",
		"Al-Nour Private Clinic",
	)
	seed = _seed_branch(company, branch, mode="clinic", patients=phase["seed_patients"], force=force)
	roles = {}
	try:
		from omnexa_healthcare.api.healthcare_role_demo import seed_healthcare_role_demo

		roles = seed_healthcare_role_demo(company=company, branch=branch)
	except Exception:
		frappe.log_error(title="Healthcare clinic phase — role demo sync")
	_set_active_phase("clinic", company, branch)
	frappe.db.commit()
	return {"phase": "clinic", "company": company, "branch": branch, "seed": seed, "roles": roles}


def _activate_hospital_phase(phase: dict, force: int) -> dict:
	company = phase["company_abbr"]
	if not frappe.db.exists("Company", company):
		company = _ensure_company(phase["company_abbr"], phase["company_name"])
	branch = f"{company}-{phase['branch_code']}"
	if not frappe.db.exists("Branch", branch):
		branch = _ensure_branch(company, phase["branch_code"], phase["branch_name"], is_head_office=1)

	from omnexa_healthcare.api.healthcare_role_demo import seed_full_healthcare_demo

	result = seed_full_healthcare_demo(company=company, branch=branch, patients=phase["seed_patients"])
	_ensure_branch_website(
		branch,
		company,
		phase["site_slug"],
		"مستشفى الحياة",
		"Al-Hayat Hospital",
	)
	_set_active_phase("hospital", company, branch)
	frappe.db.commit()
	return {"phase": "hospital", "company": company, "branch": branch, **result}


def _activate_national_phase(force: int) -> dict:
	holding = _ensure_company("MH-EG", "الهيئة الوطنية للرعاية الصحية")
	holding_branch = _ensure_branch(holding, "HO", "المقر المركزي", is_head_office=1)
	_ensure_branch_website(
		holding_branch,
		holding,
		"mh-eg",
		"الهيئة الوطنية للرعاية الصحية",
		"National Health Authority",
	)

	seed_results: list[dict] = []
	for gov in NATIONAL_GOVERNORATES:
		company = _ensure_company(gov["abbr"], gov["name_ar"])
		first_branch = None
		for idx, spec in enumerate(gov["branches"]):
			branch = _ensure_branch(
				company,
				spec["code"],
				spec["name_ar"],
				is_head_office=cint(idx == 0),
			)
			if not first_branch:
				first_branch = branch
			_ensure_branch_website(
				branch,
				company,
				spec["site_slug"],
				spec["name_ar"],
				spec["name_ar"],
			)
			if cint(force) or not frappe.db.exists(
				"Healthcare Facility Profile",
				{"company": company, "branch": branch, "facility_type": spec["facility"]},
			):
				try:
					seed_results.append(
						{
							"branch": branch,
							**_seed_branch(
								company,
								branch,
								mode=spec["seed_mode"],
								patients=spec["patients"],
								force=force,
							),
						}
					)
				except Exception:
					frappe.log_error(title=f"National demo seed failed: {branch}")

	from omnexa_healthcare.api.healthcare_role_demo import seed_healthcare_role_demo

	roles = seed_healthcare_role_demo(company=holding, branch=holding_branch)
	_set_active_phase("national", holding, holding_branch)
	frappe.db.commit()
	return {
		"phase": "national",
		"company": holding,
		"branch": holding_branch,
		"network": _national_network_status(),
		"seed_results": seed_results,
		"roles": roles,
	}


@frappe.whitelist()
def activate_deployment_phase(phase_id: str, force: int = 1) -> dict:
	"""Provision master data + demo seed for a deployment phase."""
	frappe.only_for("System Manager")
	phase = _phase_by_id((phase_id or "").strip().lower())
	force = cint(force)

	if phase["id"] == "clinic":
		return _activate_clinic_phase(phase, force)
	if phase["id"] == "hospital":
		return _activate_hospital_phase(phase, force)
	if phase["id"] == "national":
		return _activate_national_phase(force)
	frappe.throw(_("Unsupported phase"))


@frappe.whitelist()
def set_deployment_phase_context(phase_id: str) -> dict:
	"""Switch user defaults to a phase without re-seeding."""
	frappe.only_for("System Manager")
	phase = _phase_by_id((phase_id or "").strip().lower())
	company, branch = _resolve_company_branch(phase)
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} is not provisioned. Activate the phase first.").format(company))
	if not frappe.db.exists("Branch", branch):
		frappe.throw(_("Branch {0} is not provisioned. Activate the phase first.").format(branch))
	_set_active_phase(phase["id"], company, branch)
	frappe.db.commit()
	return {"ok": True, "phase": phase["id"], "company": company, "branch": branch}
