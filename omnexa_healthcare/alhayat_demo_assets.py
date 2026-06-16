# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Al-Hayat hospital demo branding assets (bundled + editable via DocTypes)."""

from __future__ import annotations

from omnexa_healthcare.world_class_demo_catalog import DEPARTMENTS

# Bundled mockup images — editable by replacing Attach Image on Branch Website / Department / Service.
ALHAYAT_ASSET_BASE = "/assets/omnexa_healthcare/images/alhayat"

HERO_IMAGE = f"{ALHAYAT_ASSET_BASE}/hero-landing.png"
CLINIC_CARDIOLOGY_IMAGE = f"{ALHAYAT_ASSET_BASE}/clinic-cardiology.png"
DOCTORS_BANNER_IMAGE = f"{ALHAYAT_ASSET_BASE}/doctors-team.png"

SERVICE_IMAGES = {
	"Pharmacy": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=900&q=80",
	"Radiology": "https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=900&q=80",
	"Laboratory": "https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&w=900&q=80",
	"Emergency": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=900&q=80",
}

DOCTOR_PHOTOS = [
	"https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=600&q=80",
	"https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=600&q=80",
	"https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=600&q=80",
	"https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=600&q=80",
	"https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=600&q=80",
	"https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&w=600&q=80",
]

DEPARTMENT_IMAGES = {
	"CARD": CLINIC_CARDIOLOGY_IMAGE,
	"PED": CLINIC_CARDIOLOGY_IMAGE,
	"ORT": CLINIC_CARDIOLOGY_IMAGE,
	"RAD": SERVICE_IMAGES["Radiology"],
	"LAB": SERVICE_IMAGES["Laboratory"],
	"ER": SERVICE_IMAGES["Emergency"],
	"PHM": SERVICE_IMAGES["Pharmacy"],
}

ALHAYAT_COPY = {
	"hospital_name_ar": "مستشفى الحياة",
	"hospital_name_en": "Al-Hayat Hospital",
	"tagline_ar": "رعايتكم... أولويتنا مستشفى الحياة",
	"tagline_en": "Your care... our priority — Al-Hayat Hospital",
	"hero_text_ar": (
		"مستشفى متعدد التخصصات يقدم رعاية صحية شاملة بأحدث التقنيات الطبية "
		"وعيادات تخصصية وكادر طبي مؤهل على مدار الساعة."
	),
	"hero_text_en": (
		"A multi-specialty hospital delivering comprehensive care with modern technology, "
		"specialty clinics, and a qualified medical team."
	),
	"working_hours_ar": "السبت - الخميس: 9:00 ص - 8:00 م | الجمعة: 2:00 م - 8:00 م",
	"working_hours_en": "Sat-Thu: 9:00 AM - 8:00 PM | Fri: 2:00 PM - 8:00 PM",
	"stat_years": 15,
	"stat_doctors": 120,
	"stat_patients": 250000,
	"stat_departments": 39,
}


def _default_department_copy(code: str, label: str) -> dict[str, str]:
	return {
		"website_description_ar": f"قسم {label} — رعاية متخصصة بمعايير مستشفى عالمي.",
		"website_description_en": f"{label} — specialized care at world-class hospital standards.",
		"website_services_ar": f"استشارات {label}\nفحوصات تشخيصية\nمتابعة علاجية\nتنسيق مع أقسام المستشفى",
		"website_services_en": f"{label} consultations\nDiagnostic workup\nTreatment follow-up\nHospital care coordination",
	}


DEPARTMENT_COPY: dict[str, dict[str, str]] = {
	code: _default_department_copy(code, label) for code, label, _ut in DEPARTMENTS
}

DEPARTMENT_COPY["CARD"] = {
	"website_description_ar": "عيادة القلب والأوعية الدموية — تشخيص وعلاج شامل بأحدث التقنيات.",
	"website_description_en": "Cardiology clinic — comprehensive diagnosis and treatment with modern technology.",
	"website_services_ar": "رسم القلب\nموجات فوق صوتية للقلب\nعلاج قصور القلب\nتركيب دعامات الشرايين\nمتابعة ارتفاع ضغط الدم",
	"website_services_en": "ECG\nEchocardiogram\nHeart failure treatment\nStent placement\nHypertension follow-up",
}

DEPARTMENT_COPY["ER"] = {
	"website_description_ar": "قسم الطوارئ — استقبال الحالات الحرجة على مدار 24 ساعة.",
	"website_description_en": "Emergency department — 24/7 critical care intake and triage.",
	"website_services_ar": "فرز طبي\nإنعاش\nحوادث\nإصابات\nاستقرار وتحويل",
	"website_services_en": "Medical triage\nResuscitation\nTrauma\nInjuries\nStabilization & transfer",
}

DEPARTMENT_COPY["IVF"] = {
	"website_description_ar": "مركز الخصوبة وأطفال الأنابيب — بروتوكولات علاج متقدمة.",
	"website_description_en": "Fertility & IVF center — advanced reproductive medicine protocols.",
	"website_services_ar": "استشارة خصوبة\nتحفيز المبايض\nأطفال أنابيب\nمتابعة حمل\nاستشارة وراثية",
	"website_services_en": "Fertility consultation\nOvulation induction\nIVF cycles\nPregnancy monitoring\nGenetic counseling",
}
