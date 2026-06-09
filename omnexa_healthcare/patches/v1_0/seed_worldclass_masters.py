# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Seed ICD-10 samples, imaging modalities, and specialty clinical templates."""

import frappe

ICD10 = [
	("J06.9", "Acute upper respiratory infection, unspecified"),
	("I10", "Essential (primary) hypertension"),
	("E11.9", "Type 2 diabetes mellitus without complications"),
	("M54.5", "Low back pain"),
	("Z00.00", "Encounter for general adult medical examination"),
	("F32.9", "Major depressive disorder, single episode, unspecified"),
	("H52.4", "Presbyopia"),
	("K02.9", "Dental caries, unspecified"),
]

MODALITIES = [
	("CT", "Computed Tomography", "CT"),
	("MR", "Magnetic Resonance", "MR"),
	("XR", "X-Ray", "XR"),
	("US", "Ultrasound", "US"),
	("MG", "Mammography", "MG"),
]

SPECIALTIES = [
	("GEN", "General Medicine", "Subjective / Objective / Assessment / Plan"),
	("PED", "Pediatrics", "Growth · Immunization · SOAP"),
	("OBG", "OB/GYN", "Obstetric History · LMP · Plan"),
	("DER", "Dermatology", "Lesion Description · Distribution · Plan"),
	("ENT", "ENT", "Ear · Nose · Throat Exam"),
	("OPH", "Ophthalmology", "Visual Acuity · IOP · Fundoscopy"),
	("DENT", "Dental", "Tooth Chart · Periodontal · Treatment Plan"),
	("ORT", "Orthopedics", "Joint Exam · ROM · Imaging"),
	("CAR", "Cardiology", "Cardiac History · ECG · Echo"),
	("PSY", "Psychiatry", "MSE · Risk Assessment · Plan"),
]


def execute():
	for code, desc in ICD10:
		if frappe.db.exists("Healthcare Icd10 Code", {"code": code}):
			continue
		frappe.get_doc({"doctype": "Healthcare Icd10 Code", "code": code, "description": desc, "is_active": 1}).insert(
			ignore_permissions=True
		)
	for code, name, dicom in MODALITIES:
		if frappe.db.exists("Healthcare Imaging Modality", {"modality_code": code}):
			continue
		frappe.get_doc(
			{"doctype": "Healthcare Imaging Modality", "modality_code": code, "modality_name": name, "dicom_modality": dicom, "is_active": 1}
		).insert(ignore_permissions=True)
	company = frappe.db.get_value("Company", {}, "name")
	if company:
		for spec_code, spec_name, template_body in SPECIALTIES:
			if not frappe.db.exists("Healthcare Specialty", spec_code):
				frappe.get_doc(
					{"doctype": "Healthcare Specialty", "specialty_code": spec_code, "specialty_name": spec_name, "is_active": 1}
				).insert(ignore_permissions=True)
			if not frappe.db.exists("Healthcare Clinical Template", {"specialty": spec_code, "company": company}):
				frappe.get_doc(
					{
						"doctype": "Healthcare Clinical Template",
						"specialty": spec_code,
						"template_name": f"{spec_name} SOAP",
						"assessment_template": template_body,
						"company": company,
						"is_active": 1,
					}
				).insert(ignore_permissions=True)
