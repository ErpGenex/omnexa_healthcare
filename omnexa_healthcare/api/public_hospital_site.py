# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Public hospital / clinic website APIs."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, get_url

from omnexa_healthcare.api.web_booking import get_published_services
from omnexa_healthcare.scheduling_engine import get_available_slots

try:
	from omnexa_healthcare.alhayat_demo_assets import HERO_IMAGE as DEFAULT_HERO_IMAGE
except Exception:
	DEFAULT_HERO_IMAGE = (
		"https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80"
	)


def _public_url(path: str | None) -> str:
	if not path:
		return ""
	if path.startswith(("http://", "https://", "/assets/")):
		return get_url(path) if path.startswith("/") else path
	return get_url(path)

DEPARTMENT_ICONS = {
	"general": "🏥",
	"cardiology": "❤️",
	"orthopedics": "🦴",
	"pediatrics": "👶",
	"obgyn": "🤰",
	"internal": "🩺",
	"ent": "👂",
	"dermatology": "✨",
	"ophthalmology": "👁️",
	"dentistry": "🦷",
	"emergency": "🚑",
	"lab": "🔬",
	"radiology": "📷",
	"pharmacy": "💊",
}

_DEMO_NAME_PREFIXES = ("DEMO-HC-", "DEMO-HC ", "HC-DEMO-", "HC-DEMO ")


def _strip_demo_prefix(value: str) -> str:
	text = (value or "").strip()
	for prefix in _DEMO_NAME_PREFIXES:
		if text.startswith(prefix):
			return text[len(prefix) :].strip()
	return text


def _apply_department_doctor_filter(
	department: str,
	*,
	conditions: list[str],
	params: list,
) -> None:
	dept = frappe.db.get_value(
		"Healthcare Department",
		department,
		["department_name", "department_code"],
		as_dict=True,
	)
	if not dept:
		return

	practitioners = frappe.get_all(
		"Healthcare Service Catalog",
		filters={
			"department": department,
			"is_active": 1,
			"publish_on_website": 1,
			"default_practitioner": ["is", "set"],
		},
		pluck="default_practitioner",
	)
	practitioners = list({name for name in practitioners if name})
	if practitioners:
		conditions.append(f"p.name IN ({', '.join(['%s'] * len(practitioners))})")
		params.extend(practitioners)
		return

	name_token = _strip_demo_prefix(dept.department_name or "")
	code_token = _strip_demo_prefix(dept.department_code or "")
	conditions.append(
		"(pb.specialty IN (SELECT name FROM `tabHealthcare Specialty` WHERE specialty_name LIKE %s OR specialty_code LIKE %s) "
		"OR s.specialty_name LIKE %s OR s.specialty_code LIKE %s OR pb.specialty LIKE %s)"
	)
	params.extend([f"%{name_token}%", f"%{code_token}%", f"%{name_token}%", f"%{code_token}%", f"%{code_token}%"])


def _default_hospital_context() -> dict | None:
	"""Resolve tenant when /hospital is opened without query params."""
	if frappe.db.exists("DocType", "Healthcare Branch Website"):
		rows = frappe.get_all(
			"Healthcare Branch Website",
			filters={"is_enabled": 1},
			fields=["name", "branch", "company", "site_slug"],
			order_by="modified desc",
			limit=1,
		)
		if rows:
			return rows[0]

	company = (
		frappe.defaults.get_global_default("company")
		or frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	)
	if not company:
		return None
	branch = frappe.db.get_value("Branch", {"company": company}, "name", order_by="creation asc")
	return {"name": None, "branch": branch, "company": company}


def _resolve_site(*, site: str | None = None, company: str | None = None, branch: str | None = None) -> dict:
	if site:
		row = frappe.db.get_value(
			"Healthcare Branch Website",
			{"site_slug": site.strip().lower(), "is_enabled": 1},
			["name", "branch", "company"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Hospital website not found or disabled."), frappe.DoesNotExistError)
		return row

	if branch:
		branch_company = frappe.db.get_value("Branch", branch, "company")
		if not branch_company:
			frappe.throw(_("Branch not found."))
		if company and branch_company != company:
			frappe.throw(_("Branch does not belong to company."))
		website = frappe.db.get_value(
			"Healthcare Branch Website",
			{"branch": branch, "is_enabled": 1},
			["name", "branch", "company"],
			as_dict=True,
		)
		if website:
			return website
		return {"name": None, "branch": branch, "company": branch_company or company}

	if company:
		websites = frappe.get_all(
			"Healthcare Branch Website",
			filters={"company": company, "is_enabled": 1},
			fields=["name", "branch", "company"],
			order_by="modified desc",
			limit=1,
		)
		if websites:
			return websites[0]
		branch = frappe.db.get_value("Branch", {"company": company}, "name")
		if branch:
			return {"name": None, "branch": branch, "company": company}

	ctx = _default_hospital_context()
	if ctx:
		if branch:
			ctx["branch"] = branch
		if company and ctx.get("company") and company != ctx["company"]:
			frappe.throw(_("Branch does not belong to company."))
		if company:
			ctx["company"] = company
		return ctx

	frappe.throw(_("Site, branch or company is required."))


def _website_doc(branch: str) -> frappe._dict | None:
	name = frappe.db.get_value("Healthcare Branch Website", {"branch": branch})
	if not name:
		return None
	return frappe.get_doc("Healthcare Branch Website", name)


def _site_query(site: str | None = None) -> str:
	return f"site={site}" if site else ""


def build_public_urls(*, branch: str, site_slug: str | None = None) -> dict:
	slug = site_slug or frappe.db.get_value("Healthcare Branch Website", {"branch": branch}, "site_slug")
	q = _site_query(slug)
	base = get_url("/hospital")
	join = "?" if q else ""
	suffix = f"{join}{q}" if q else ""
	return {
		"home": f"{base}{suffix}",
		"doctors": f"{base}/doctors{suffix}",
		"booking": f"{base}/booking{suffix}",
		"clinic": f"{base}/clinic{suffix}",
		"shop": f"{base}/shop{suffix}",
		"legacy_booking": get_url(f"/healthcare-booking?company={frappe.db.get_value('Branch', branch, 'company')}&branch={branch}"),
	}


def _live_stats(branch: str, company: str, website: frappe._dict | None) -> dict:
	dept_count = frappe.db.count(
		"Healthcare Department",
		{"branch": branch, "status": "Active", "publish_on_website": 1},
	)
	doc_count = frappe.db.sql(
		"""
		SELECT COUNT(DISTINCT p.name)
		FROM `tabHealthcare Practitioner` p
		INNER JOIN `tabHealthcare Practitioner Branch` pb ON pb.parent = p.name
		WHERE p.company = %s AND p.status = 'Active' AND IFNULL(p.publish_on_website, 0) = 1
			AND pb.branch = %s AND IFNULL(pb.is_active, 0) = 1
		""",
		(company, branch),
	)[0][0]
	patient_count = frappe.db.count("Healthcare Patient", {"branch": branch, "active": 1})

	def pick(field: str, live: int) -> int:
		val = cint(getattr(website, field, 0) if website else 0)
		return val or live

	return {
		"departments": pick("stat_departments", dept_count),
		"doctors": pick("stat_doctors", doc_count),
		"patients": pick("stat_patients", patient_count),
		"years": pick("stat_years", 10),
	}


@frappe.whitelist(allow_guest=True)
def get_site_config(site: str | None = None, company: str | None = None, branch: str | None = None) -> dict:
	ctx = _resolve_site(site=site, company=company, branch=branch)
	branch = ctx.branch
	company = ctx.company
	website = _website_doc(branch)
	if website and not website.is_enabled:
		frappe.throw(_("Hospital website is disabled."))

	urls = build_public_urls(branch=branch, site_slug=website.site_slug if website else None)
	stats = _live_stats(branch, company, website)

	if frappe.db.exists("DocType", "Experience Portal Hub"):
		portal_slug = frappe.db.get_value("Experience Portal Hub", {"company": company, "is_enabled": 1}, "site_slug")
		if portal_slug:
			urls["unified_portal"] = get_url(f"/portal?site={portal_slug}")
		else:
			urls["unified_portal"] = get_url(f"/portal?company={company}")

	name_ar = website.hospital_name_ar if website else branch
	name_en = website.hospital_name_en if website else branch
	return {
		"branch": branch,
		"company": company,
		"site_slug": website.site_slug if website else None,
		"hospital_name_ar": name_ar,
		"hospital_name_en": name_en,
		"tagline_ar": (website.tagline_ar if website else "") or "رعايتكم... أولويتنا",
		"tagline_en": (website.tagline_en if website else "") or "Your care... our priority",
		"hero_text_ar": website.hero_text_ar if website else "",
		"hero_text_en": website.hero_text_en if website else "",
		"hero_image": _public_url((website.hero_image if website else "") or DEFAULT_HERO_IMAGE),
		"logo": _public_url(website.website_logo if website else ""),
		"primary_color": (website.primary_color if website else "") or "#003366",
		"contact": {
			"phone": website.contact_phone if website else "",
			"email": website.contact_email if website else "",
			"address_ar": website.contact_address_ar if website else "",
			"address_en": website.contact_address_en if website else "",
		},
		"working_hours_ar": website.working_hours_ar if website else "",
		"working_hours_en": website.working_hours_en if website else "",
		"stats": stats,
		"features": {
			"shop": cint(website.enable_online_shop if website else 1),
			"doctors": cint(website.enable_doctors_page if website else 1),
			"departments": cint(website.enable_departments_page if website else 1),
		},
		"social": {
			"facebook": website.facebook_url if website else "",
			"instagram": website.instagram_url if website else "",
			"whatsapp": website.whatsapp_number if website else "",
		},
		"urls": urls,
	}


@frappe.whitelist()
def get_site_urls(branch: str) -> dict:
	if not branch:
		frappe.throw(_("Branch is required"))
	if not frappe.has_permission("Healthcare Branch Website", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	website = _website_doc(branch)
	slug = website.site_slug if website else None
	urls = build_public_urls(branch=branch, site_slug=slug)
	return {
		"branch": branch,
		"site_slug": slug,
		"public_url": urls["home"],
		"urls": urls,
	}


@frappe.whitelist(allow_guest=True)
def get_published_departments(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
) -> list[dict]:
	ctx = _resolve_site(site=site, company=company, branch=branch)
	rows = frappe.get_all(
		"Healthcare Department",
		filters={"branch": ctx.branch, "status": "Active", "publish_on_website": 1},
		fields=[
			"name",
			"department_name",
			"department_code",
			"website_icon",
			"website_image",
			"website_description_ar",
			"website_description_en",
			"website_display_order",
			"website_services_ar",
			"website_services_en",
		],
		order_by="website_display_order asc, department_name asc",
	)
	for row in rows:
		icon_key = (row.pop("website_icon", None) or "general").lower()
		row["icon"] = DEPARTMENT_ICONS.get(icon_key, DEPARTMENT_ICONS["general"])
		row["services_ar"] = [line.strip() for line in (row.pop("website_services_ar") or "").splitlines() if line.strip()]
		row["services_en"] = [line.strip() for line in (row.pop("website_services_en") or "").splitlines() if line.strip()]
		row["image"] = _public_url(row.pop("website_image", None))
	return rows


@frappe.whitelist(allow_guest=True)
def get_department_clinic(
	department: str,
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
) -> dict:
	"""Single department/clinic page payload for public hospital site."""
	ctx = _resolve_site(site=site, company=company, branch=branch)
	if not frappe.db.exists("Healthcare Department", department):
		frappe.throw(_("Department not found."), frappe.DoesNotExistError)
	row = frappe.db.get_value(
		"Healthcare Department",
		department,
		[
			"name",
			"branch",
			"department_name",
			"department_code",
			"website_icon",
			"website_image",
			"website_description_ar",
			"website_description_en",
			"website_services_ar",
			"website_services_en",
		],
		as_dict=True,
	)
	if not row or row.branch != ctx.branch:
		frappe.throw(_("Department not found."), frappe.DoesNotExistError)
	icon_key = (row.website_icon or "general").lower()
	services_ar = [line.strip() for line in (row.website_services_ar or "").splitlines() if line.strip()]
	services_en = [line.strip() for line in (row.website_services_en or "").splitlines() if line.strip()]
	website = _website_doc(ctx.branch)
	return {
		"name": row.name,
		"department_name": row.department_name,
		"department_code": row.department_code,
		"icon": DEPARTMENT_ICONS.get(icon_key, DEPARTMENT_ICONS["general"]),
		"image": _public_url(row.website_image),
		"description_ar": row.website_description_ar,
		"description_en": row.website_description_en,
		"services_ar": services_ar,
		"services_en": services_en,
		"working_hours_ar": (website.working_hours_ar if website else ""),
		"working_hours_en": (website.working_hours_en if website else ""),
		"booking_url": build_public_urls(branch=ctx.branch, site_slug=website.site_slug if website else None)["booking"],
	}


@frappe.whitelist(allow_guest=True)
def get_published_doctors(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
	department: str | None = None,
	specialty: str | None = None,
) -> list[dict]:
	ctx = _resolve_site(site=site, company=company, branch=branch)
	conditions = [
		"p.company = %s",
		"p.status = 'Active'",
		"IFNULL(p.publish_on_website, 0) = 1",
		"pb.branch = %s",
		"IFNULL(pb.is_active, 0) = 1",
	]
	params: list = [ctx.company, ctx.branch]

	if specialty:
		conditions.append("pb.specialty = %s")
		params.append(specialty)
	if department:
		_apply_department_doctor_filter(department, conditions=conditions, params=params)

	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT
			p.name,
			p.practitioner_name,
			p.license_number,
			p.website_photo,
			p.years_of_experience,
			p.website_rating,
			p.website_bio_ar,
			p.website_bio_en,
			pb.specialty,
			pb.consultation_fee,
			s.specialty_name
		FROM `tabHealthcare Practitioner` p
		INNER JOIN `tabHealthcare Practitioner Branch` pb ON pb.parent = p.name
		LEFT JOIN `tabHealthcare Specialty` s ON s.name = pb.specialty
		WHERE {" AND ".join(conditions)}
		ORDER BY p.practitioner_name asc
		""",
		params,
		as_dict=True,
	)

	out = []
	services = get_published_services(ctx.company, ctx.branch)
	services_by_practitioner: dict[str, list[str]] = {}
	services_by_department: dict[str, list[str]] = {}
	for service in services:
		code = service.get("service_code")
		if not code:
			continue
		pr = service.get("default_practitioner")
		if pr:
			services_by_practitioner.setdefault(pr, []).append(code)
		dep = service.get("department")
		if dep:
			services_by_department.setdefault(dep, []).append(code)

	for row in rows:
		service_codes = services_by_practitioner.get(row.name) or []
		if not service_codes and department:
			service_codes = services_by_department.get(department, [])[:3]
		out.append(
			{
				"name": row.name,
				"practitioner_name": row.practitioner_name,
				"license_number": row.license_number,
				"photo": _public_url(row.website_photo),
				"years_of_experience": cint(row.years_of_experience) or 5,
				"rating": flt(row.website_rating) or 4.8,
				"bio_ar": row.website_bio_ar,
				"bio_en": row.website_bio_en,
				"specialty": row.specialty,
				"specialty_name": row.specialty_name or row.specialty,
				"consultation_fee": flt(row.consultation_fee),
				"service_codes": service_codes[:3],
			}
		)
	return out


@frappe.whitelist(allow_guest=True)
def get_practitioner_booking_slots(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
	practitioner: str | None = None,
	date: str | None = None,
	specialty: str | None = None,
) -> dict:
	ctx = _resolve_site(site=site, company=company, branch=branch)
	if not (practitioner and date):
		frappe.throw(_("Practitioner and date are required"))

	if frappe.db.get_value("Healthcare Practitioner", practitioner, "company") != ctx.company:
		frappe.throw(_("Practitioner not found."))

	slots = get_available_slots(practitioner, ctx.branch, date, specialty=specialty, include_walk_in=True)
	return {
		"practitioner": practitioner,
		"practitioner_name": frappe.db.get_value("Healthcare Practitioner", practitioner, "practitioner_name"),
		"slots": slots,
	}


@frappe.whitelist(allow_guest=True)
def get_shop_items(
	site: str | None = None,
	company: str | None = None,
	branch: str | None = None,
) -> dict:
	ctx = _resolve_site(site=site, company=company, branch=branch)
	services = get_published_services(ctx.company, ctx.branch)
	products: list[dict] = []
	if frappe.db.table_exists("tabCatalog Item"):
		products = frappe.get_all(
			"Catalog Item",
			filters={"company": ctx.company, "published": 1},
			fields=["name", "slug", "title_en", "title_ar", "item_type"],
			limit=24,
			order_by="modified desc",
		)
	return {"services": services, "products": products, "has_experience": bool(products)}
