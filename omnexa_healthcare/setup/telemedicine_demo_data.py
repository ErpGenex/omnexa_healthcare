# -*- coding: utf-8 -*-
"""Seed realistic telemedicine demo data for QA and portal testing."""

import frappe
from frappe.utils import add_to_date, now_datetime


DEMO_DOCTORS = [
	{"given": "Tele", "family": "Doctor One", "email": "tele.doctor1@mh.local", "phone": "+201010000001", "specialty_slug": "general"},
	{"given": "Tele", "family": "Doctor Two", "email": "tele.doctor2@mh.local", "phone": "+201010000002", "specialty_slug": "cardiology"},
	{"given": "Tele", "family": "Doctor Three", "email": "tele.doctor3@mh.local", "phone": "+201010000003", "specialty_slug": "dermatology"},
	{"given": "Tele", "family": "Doctor Four", "email": "tele.doctor4@mh.local", "phone": "+201010000004", "specialty_slug": "pediatrics"},
	{"given": "Tele", "family": "Doctor Five", "email": "tele.doctor5@mh.local", "phone": "+201010000005", "specialty_slug": "general"},
	{"given": "Tele", "family": "Doctor Six", "email": "tele.doctor6@mh.local", "phone": "+201010000006", "specialty_slug": "dermatology"},
]

DEMO_DEPARTMENTS = [
	{"code": "TELE-GEN", "name": "Telemedicine General", "name_ar": "طب عن بعد - عام", "icon": "general"},
	{"code": "TELE-CARD", "name": "Telemedicine Cardiology", "name_ar": "طب عن بعد - قلب", "icon": "cardiology"},
	{"code": "TELE-DERM", "name": "Telemedicine Dermatology", "name_ar": "طب عن بعد - جلدية", "icon": "dermatology"},
	{"code": "TELE-PED", "name": "Telemedicine Pediatrics", "name_ar": "طب عن بعد - أطفال", "icon": "pediatrics"},
]

DEMO_RADIOLOGY_PROCEDURES = [
	{"code": "XR-CHEST", "name": "Chest X-Ray", "modality": "X-Ray"},
	{"code": "XR-ABD", "name": "Abdominal X-Ray", "modality": "X-Ray"},
	{"code": "US-ABD", "name": "Abdominal Ultrasound", "modality": "Ultrasound"},
	{"code": "CT-HEAD", "name": "Head CT Scan", "modality": "CT"},
	{"code": "MRI-SPINE", "name": "Spine MRI", "modality": "MRI"},
	{"code": "MAMMO-SCREEN", "name": "Mammography Screening", "modality": "Mammography"},
]

DEMO_PATIENTS = [
	{"given": "Tele", "family": "Patient Alpha", "email": "tele.patient1@mh.local", "phone": "+201020000001"},
	{"given": "Tele", "family": "Patient Beta", "email": "tele.patient2@mh.local", "phone": "+201020000002"},
	{"given": "Tele", "family": "Patient Gamma", "email": "tele.patient3@mh.local", "phone": "+201020000003"},
	{"given": "Tele", "family": "Patient Delta", "email": "tele.patient4@mh.local", "phone": "+201020000004"},
]


def setup(force=False):
	"""Ensure config, demo users, practitioners, patients, and sessions."""
	frappe.only_for(("System Manager", "Company Admin"))

	from omnexa_healthcare.api.telemedicine_admin import ensure_telemedicine_configuration

	ensure_telemedicine_configuration()
	company, branch = _get_company_branch()
	departments = _ensure_telemedicine_departments(company, branch)
	radiology = _ensure_radiology_procedures(company)
	specialty = _get_specialty()
	practitioners = _ensure_demo_practitioners(company, branch, specialty)
	patients = _ensure_demo_patients(company, branch)
	result = seed(force=force, practitioners=practitioners, patients=patients, company=company, branch=branch)
	result["departments"] = [d.name for d in departments]
	result["radiology_procedures"] = [p.name for p in radiology]
	result["demo_users"] = {
		"doctors": [d["email"] for d in DEMO_DOCTORS],
		"patients": [p["email"] for p in DEMO_PATIENTS],
		"password": "Tele@12345",
	}
	return result


def seed(force=False, practitioners=None, patients=None, company=None, branch=None):
	"""Create telemedicine sessions, queue entries, devices, and readings."""
	frappe.only_for(("System Manager", "Company Admin"))

	if not force and frappe.db.count("Healthcare Telemedicine Session", {"room_id": ["like", "tele_demo_%"]}):
		return {
			"success": True,
			"skipped": True,
			"message": "Telemedicine demo sessions already exist. Pass force=True to recreate.",
		}

	company = company or _get_company_branch()[0]
	branch = branch or _get_company_branch()[1]
	practitioners = practitioners or _resolve_practitioners(company)
	patients = patients or _resolve_patients(company, branch)

	if force:
		_clear_demo_sessions()
		_clear_demo_devices()

	created = {"sessions": [], "devices": [], "readings": []}
	now = now_datetime()

	scenarios = [
		{"offset_hours": 2, "status": "Scheduled", "session_type": "Video", "rating": 0},
		{"offset_hours": 1, "status": "Scheduled", "session_type": "Voice", "rating": 0},
		{"offset_hours": 0, "status": "In Progress", "session_type": "Video", "rating": 0},
		{"offset_hours": -2, "status": "Completed", "session_type": "Video", "rating": 5, "quality": "Excellent"},
		{"offset_hours": -4, "status": "Completed", "session_type": "Chat", "rating": 4, "quality": "Good"},
		{"offset_hours": -6, "status": "Completed", "session_type": "Voice", "rating": 5, "quality": "Good"},
		{"offset_hours": -24, "status": "Cancelled", "session_type": "Video", "rating": 0},
		{"offset_hours": -48, "status": "No Show", "session_type": "Video", "rating": 0},
	]

	for index, scenario in enumerate(scenarios):
		patient = patients[index % len(patients)]
		practitioner = practitioners[index % len(practitioners)]
		scheduled = add_to_date(now, hours=scenario["offset_hours"])

		session = frappe.get_doc(
			{
				"doctype": "Healthcare Telemedicine Session",
				"patient": patient.name if hasattr(patient, "name") else patient["name"],
				"practitioner": practitioner.name if hasattr(practitioner, "name") else practitioner["name"],
				"company": company,
				"branch": branch,
				"session_type": scenario["session_type"],
				"scheduled_datetime": scheduled,
				"status": scenario["status"],
				"room_id": f"tele_demo_{index + 1:03d}",
				"clinical_notes": f"Demo telemedicine session #{index + 1}",
			}
		)

		if scenario["status"] in ("In Progress", "Completed"):
			session.start_datetime = add_to_date(scheduled, minutes=-5)
		if scenario["status"] == "Completed":
			session.end_datetime = add_to_date(scheduled, minutes=25)
			session.duration_minutes = 30
			session.rating = scenario["rating"]
			session.technical_quality = scenario.get("quality")
			session.patient_feedback = "Excellent remote consultation experience."
		if scenario["status"] == "Cancelled":
			session.clinical_notes = "Cancelled by patient request."

		session.insert(ignore_permissions=True)
		created["sessions"].append(session.name)

		if scenario["status"] in ("Scheduled", "In Progress"):
			queue_status = "Waiting" if scenario["status"] == "Scheduled" else "In Progress"
			frappe.get_doc(
				{
					"doctype": "Healthcare Telemedicine Queue",
					"practitioner": session.practitioner,
					"session": session.name,
					"queue_position": index + 1,
					"status": queue_status,
					"joined_datetime": scheduled,
					"estimated_wait_minutes": max(0, index * 5),
					"company": company,
					"branch": branch,
				}
			).insert(ignore_permissions=True)

	for index, patient in enumerate(patients[:4]):
		patient_id = patient.name if hasattr(patient, "name") else patient["name"]
		device = frappe.get_doc(
			{
				"doctype": "Healthcare Remote Monitoring Device",
				"device_name": f"Blood Pressure Monitor {index + 1}",
				"device_type": "Blood Pressure Monitor",
				"manufacturer": "OmniHealth",
				"model": "BP-200",
				"serial_number": f"DEMO-BP-{index + 1:03d}",
				"patient": patient_id,
				"device_identifier": f"dev_demo_{index + 1:03d}",
				"connection_type": "Bluetooth",
				"status": "Active",
				"company": company,
				"branch": branch,
				"battery_level": 85 - (index * 5),
				"last_sync_datetime": now,
			}
		)
		device.insert(ignore_permissions=True)
		created["devices"].append(device.name)

		for day_offset, value, alert in ((0, 118, "Normal"), (1, 142, "Critical"), (2, 121, "Normal")):
			reading = frappe.get_doc(
				{
					"doctype": "Healthcare Remote Monitoring Reading",
					"device_id": device.device_identifier,
					"patient": patient_id,
					"metric_type": "Blood Pressure",
					"value": value,
					"unit": "mmHg",
					"reading_datetime": add_to_date(now, days=-day_offset, as_datetime=True),
					"alert_level": alert,
					"company": company,
				}
			)
			reading.insert(ignore_permissions=True)
			created["readings"].append(reading.name)

	frappe.db.commit()
	return {
		"success": True,
		"created": created,
		"counts": {
			"sessions": len(created["sessions"]),
			"devices": len(created["devices"]),
			"readings": len(created["readings"]),
		},
	}


def _get_company_branch():
	company = frappe.db.get_value("Company", {"name": "MH"}, "name") or frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw("No company found")
	branch = frappe.db.get_value("Branch", {"name": "MH-HO"}, "name") or frappe.db.get_value(
		"Branch", {"company": company}, "name"
	)
	if not branch:
		frappe.throw("No branch found for company")
	return company, branch


def _get_specialty():
	return _get_specialty_by_slug("general") or frappe.db.get_value("Healthcare Specialty", {}, "name")


def _get_specialty_by_slug(slug):
	key = (slug or "").lower()
	mapping = {
		"general": ("GEN", "General Medicine"),
		"dermatology": ("DER", "Dermatology"),
		"cardiology": ("CAR", "Cardiology"),
		"pediatrics": ("PED", "Pediatrics"),
	}
	for candidate in mapping.get(key, ()):
		name = frappe.db.get_value("Healthcare Specialty", candidate, "name")
		if name:
			return name
		name = frappe.db.get_value("Healthcare Specialty", {"specialty_name": candidate}, "name")
		if name:
			return name
	return None


def _ensure_telemedicine_departments(company, branch):
	created = []
	for demo in DEMO_DEPARTMENTS:
		name = f"{branch}-{demo['code']}"
		if frappe.db.exists("Healthcare Department", name):
			doc = frappe.get_doc("Healthcare Department", name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Healthcare Department",
					"department_name": demo.get("name_ar") or demo["name"],
					"department_code": demo["code"],
					"company": company,
					"branch": branch,
					"status": "Active",
					"publish_on_website": 1,
					"website_icon": demo.get("icon") or "general",
					"website_description_ar": f"قسم {demo.get('name_ar') or demo['name']} للاستشارات عن بعد",
					"website_description_en": f"{demo['name']} telemedicine department",
				}
			)
			doc.insert(ignore_permissions=True)
		created.append(doc)
	return created


def _ensure_radiology_procedures(company):
	created = []
	for demo in DEMO_RADIOLOGY_PROCEDURES:
		if frappe.db.exists("Healthcare Radiology Procedure", demo["code"]):
			created.append(frappe.get_doc("Healthcare Radiology Procedure", demo["code"]))
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Radiology Procedure",
				"procedure_name": demo["name"],
				"procedure_code": demo["code"],
				"modality": demo["modality"],
				"company": company,
				"is_active": 1,
				"description": f"Demo radiology procedure {demo['name']}",
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc)
	return created


def _ensure_demo_user(given_name, family_name, email, phone, roles):
	if frappe.db.exists("User", email):
		user = email
	else:
		user_doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": given_name,
				"last_name": family_name,
				"send_welcome_email": 0,
				"mobile_no": phone,
			}
		)
		user_doc.insert(ignore_permissions=True)
		user_doc.new_password = "Tele@12345"
		user_doc.save(ignore_permissions=True)
		user = user_doc.name

	for role in roles:
		if frappe.db.exists("Role", role) and not frappe.db.exists("Has Role", {"parent": user, "role": role}):
			frappe.get_doc({"doctype": "Has Role", "parent": user, "parenttype": "User", "role": role}).insert(
				ignore_permissions=True
			)
	return user


def _ensure_demo_practitioners(company, branch, default_specialty):
	created = []
	for demo in DEMO_DOCTORS:
		row_specialty = _get_specialty_by_slug(demo.get("specialty_slug")) or default_specialty
		user = _ensure_demo_user(
			demo["given"],
			demo["family"],
			demo["email"],
			demo["phone"],
			["Physician", "Desk User"],
		)
		existing = frappe.db.get_value("Healthcare Practitioner", {"user": user}, "name")
		if existing:
			practitioner = frappe.get_doc("Healthcare Practitioner", existing)
			practitioner.status = "Active"
			practitioner.company = company
			practitioner.publish_on_website = 1
			if practitioner.branch_assignments:
				practitioner.branch_assignments[0].specialty = row_specialty
				practitioner.branch_assignments[0].branch = branch
				practitioner.branch_assignments[0].is_active = 1
			else:
				practitioner.append(
					"branch_assignments",
					{
						"branch": branch,
						"specialty": row_specialty,
						"is_active": 1,
						"consultation_fee": 350,
					},
				)
			practitioner.save(ignore_permissions=True)
		else:
			practitioner = frappe.get_doc(
				{
					"doctype": "Healthcare Practitioner",
					"practitioner_name": f"Dr. {demo['given']} {demo['family']}",
					"company": company,
					"status": "Active",
					"user": user,
					"publish_on_website": 1,
					"website_bio_ar": f"طبيب استشاري - {demo.get('specialty_slug', 'general')}",
					"website_bio_en": f"Telemedicine specialist - {demo.get('specialty_slug', 'general')}",
					"branch_assignments": [
						{
							"branch": branch,
							"specialty": row_specialty,
							"is_active": 1,
							"consultation_fee": 350,
						}
					],
				}
			)
			practitioner.insert(ignore_permissions=True)
		created.append(practitioner)
	return created


def _ensure_demo_patients(company, branch):
	created = []
	for demo in DEMO_PATIENTS:
		existing = frappe.db.get_value(
			"Healthcare Patient Telecom",
			{"value": demo["phone"], "parenttype": "Healthcare Patient"},
			"parent",
		)
		if existing:
			created.append(frappe.get_doc("Healthcare Patient", existing))
			continue

		_ensure_demo_user(demo["given"], demo["family"], demo["email"], demo["phone"], ["Patient Portal User"])

		doc = frappe.get_doc(
			{
				"doctype": "Healthcare Patient",
				"naming_series": "HP-.#####",
				"company": company,
				"branch": branch,
				"given_name": demo["given"],
				"family_name": demo["family"],
				"gender": "female",
				"birth_date": "1990-01-01",
				"active": 1,
				"registration_status": "Complete",
				"allergies_free_text": "No known drug allergies (demo)",
				"identifiers": [
					{
						"identifier_use": "official",
						"identifier_type": "MRN",
						"value": f"TEL-{demo['phone'][-6:]}",
						"is_primary_mrn": 1,
					}
				],
				"telecom": [
					{"contact_system": "phone", "contact_use": "mobile", "value": demo["phone"], "rank": 1},
					{"contact_system": "email", "contact_use": "home", "value": demo["email"], "rank": 2},
				],
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc)
	return created


def _resolve_practitioners(company):
	rows = frappe.get_all(
		"Healthcare Practitioner",
		filters={"status": "Active", "company": company},
		fields=["name", "practitioner_name"],
		limit=5,
	)
	if not rows:
		frappe.throw("No active practitioners found")
	return rows


def _resolve_patients(company, branch):
	rows = frappe.get_all(
		"Healthcare Patient",
		filters={"company": company, "branch": branch},
		fields=["name", "full_name"],
		limit=12,
	)
	if len(rows) < 3:
		frappe.throw("Need at least 3 patients in the same company/branch")
	return rows


def _clear_demo_sessions():
	for name in frappe.get_all(
		"Healthcare Telemedicine Session",
		filters={"room_id": ["like", "tele_demo_%"]},
		pluck="name",
	):
		frappe.delete_doc("Healthcare Telemedicine Session", name, force=1, ignore_permissions=True)


def _clear_demo_devices():
	for name in frappe.get_all(
		"Healthcare Remote Monitoring Device",
		filters={"serial_number": ["like", "DEMO-BP-%"]},
		pluck="name",
	):
		frappe.delete_doc("Healthcare Remote Monitoring Device", name, force=1, ignore_permissions=True)
	for name in frappe.get_all(
		"Healthcare Remote Monitoring Reading",
		filters={"device_id": ["like", "dev_demo_%"]},
		pluck="name",
	):
		frappe.delete_doc("Healthcare Remote Monitoring Reading", name, force=1, ignore_permissions=True)
