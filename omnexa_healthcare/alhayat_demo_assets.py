# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Al-Hayat hospital demo branding assets (bundled + editable via DocTypes)."""

from __future__ import annotations

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
	"PED": f"{ALHAYAT_ASSET_BASE}/clinic-cardiology.png",
	"ORT": f"{ALHAYAT_ASSET_BASE}/clinic-cardiology.png",
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
	"stat_departments": 25,
}

DEPARTMENT_COPY = {
	"CARD": {
		"website_description_ar": "عيادة القلب والأوعية الدموية — تشخيص وعلاج شامل بأحدث التقنيات.",
		"website_description_en": "Cardiology clinic — comprehensive diagnosis and treatment with modern technology.",
		"website_services_ar": "رسم القلب\nموجات فوق صوتية للقلب\nعلاج قصور القلب\nتركيب دعامات الشرايين\nمتابعة ارتفاع ضغط الدم",
		"website_services_en": "ECG\nEchocardiogram\nHeart failure treatment\nStent placement\nHypertension follow-up",
	},
}
