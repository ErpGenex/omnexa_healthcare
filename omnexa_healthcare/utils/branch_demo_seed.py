# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Branch-scoped multi-specialty hospital demo — 20 patients, all departments."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

DEMO_MARKER = "DEMO-HC-"
REPORTING_TAG = "DEMO-HC"

DEPARTMENTS: list[tuple[str, str, str]] = [
	("OPD", "Outpatient", "Clinic"),
	("CARD", "Cardiology", "Clinic"),
	("PED", "Pediatrics", "Clinic"),
	("ORT", "Orthopedics", "Clinic"),
	("DER", "Dermatology", "Clinic"),
	("DEN", "Dental Center", "Clinic"),
	("RAD", "Radiology", "Service Unit"),
	("LAB", "Laboratory", "Service Unit"),
	("PHM", "Pharmacy", "Pharmacy"),
	("ER", "Emergency", "Emergency"),
	("IPD", "Inpatient Ward", "Ward"),
	("ICU", "Intensive Care Unit", "ICU"),
	("NICU", "Neonatal ICU (Yellow Nursery)", "NICU"),
	("CMP", "Companion Lodging", "Companion Ward"),
	("SUR", "Surgery", "Service Unit"),
]

PRACTITIONERS: list[tuple[str, str, str]] = [
	("GEN", "Dr. Nadia Farouk", "General Medicine"),
	("CAR", "Dr. Omar Khalil", "Cardiology"),
	("PED", "Dr. Sara Mahmoud", "Pediatrics"),
	("ORT", "Dr. Hisham Nabil", "Orthopedics"),
	("DER", "Dr. Laila Samir", "Dermatology"),
	("DEN", "Dr. Yasmine Fathy", "Dental"),
	("ENT", "Dr. Karim Nasr", "ENT"),
	("GYN", "Dr. Hala Refaat", "Gynecology"),
	("RAD", "Dr. Youssef Anwar", "Radiology"),
	("LAB", "Dr. Mona Adel", "Laboratory"),
]

SPECIALTY_LABEL_BY_CODE: dict[str, str] = {spec: label for spec, _name, label in PRACTITIONERS}

CLINIC_ROTATION: list[tuple[str, str, str]] = [
	("OPD", "GEN", "General Medicine"),
	("CARD", "CAR", "Cardiology"),
	("PED", "PED", "Pediatrics"),
	("ORT", "ORT", "Orthopedics"),
	("DER", "DER", "Dermatology"),
	("DEN", "DEN", "Dental"),
]

DENTAL_DEMO_TEETH: list[tuple[str, str, str]] = [
	("11", "O", "caries"),
	("16", "M", "filled"),
	("26", "D", "crown"),
	("36", "Full", "root_canal"),
	("46", "B", "healthy"),
]

# patient_index, module_code, plan_type, practitioner_key
DEMO_FOLLOW_UP_ASSIGNMENTS: list[tuple[int, str, str, str]] = [
	(0, "orthopedics", "rehabilitation", "ORT"),
	(1, "gynecology", "antenatal", "GYN"),
	(2, "physiotherapy", "physiotherapy", "ORT"),
	(3, "oncology", "chemotherapy", "GEN"),
	(4, "cardiology", "chronic_care", "CAR"),
	(5, "surgery", "post_op", "GEN"),
	(6, "pediatrics", "chronic_care", "PED"),
	(7, "dermatology", "dermatology_course", "DER"),
	(8, "neurology", "chronic_care", "GEN"),
	(9, "gastroenterology", "chronic_care", "GEN"),
	(10, "ophthalmology", "post_op", "GEN"),
	(11, "urology", "post_op", "GEN"),
	(12, "psychiatry", "psychotherapy", "GEN"),
	(13, "dental", "dental", "DEN"),
	(14, "orthopedics", "post_op", "ORT"),
	(15, "gynecology", "postnatal", "GYN"),
	(16, "cardiology", "chronic_care", "CAR"),
	(17, "physiotherapy", "physiotherapy", "ORT"),
	(18, "oncology", "chemotherapy", "GEN"),
	(19, "surgery", "post_op", "GEN"),
]

TREATMENT_PACKAGES: list[tuple[str, str, str, float, list[tuple[str, float]]]] = [
	(
		f"{DEMO_MARKER}DENTAL-CHECKUP",
		"Dental Checkup Package",
		"Dental",
		500.0,
		[("Exam + Cleaning", 500.0)],
	),
	(
		f"{DEMO_MARKER}ORTHO-START",
		"Orthodontics Starter Package",
		"Dental",
		15000.0,
		[("Consultation + Records", 2000.0), ("Metal Braces Phase 1", 13000.0)],
	),
	(
		f"{DEMO_MARKER}CARDIO-SCREEN",
		"Cardiology Screening Package",
		"Cardiology",
		1200.0,
		[("ECG", 400.0), ("Echo", 800.0)],
	),
]

PATIENT_ROSTER: list[tuple[str, str, str, int]] = [
	("Ahmed", "Hassan", "male", 1982),
	("Fatma", "Ali", "female", 1990),
	("Mohamed", "Ibrahim", "male", 1975),
	("Nour", "Said", "female", 2005),
	("Khaled", "Mostafa", "male", 1968),
	("Mariam", "Youssef", "female", 1988),
	("Tarek", "Fouad", "male", 1995),
	("Hana", "Karim", "female", 2010),
	("Yasser", "Hamdy", "male", 1979),
	("Dina", "Ashraf", "female", 1993),
	("Samir", "Lotfy", "male", 1965),
	("Rania", "Ezz", "female", 1986),
	("Hossam", "Gamal", "male", 2000),
	("Salma", "Reda", "female", 1972),
	("Amr", "Zaki", "male", 1998),
	("Nada", "Hesham", "female", 2008),
	("Walid", "Osman", "male", 1980),
	("Heba", "Magdy", "female", 1991),
	("Karim", "Badr", "male", 1970),
	("Layla", "Nasser", "female", 1984),
]

PHARMACY_ITEMS: list[tuple[str, str, float]] = [
	("PARA500", "Paracetamol 500mg", 12.0),
	("AMOX500", "Amoxicillin 500mg", 28.0),
	("METF500", "Metformin 500mg", 18.0),
	("IBU400", "Ibuprofen 400mg", 15.0),
	("SALBUT", "Salbutamol Inhaler", 65.0),
	("GLOVES", "Exam Gloves (box)", 45.0),
	("SYRINGE", "Disposable Syringe 5ml", 8.0),
	("GAUZE", "Sterile Gauze Pack", 22.0),
]

_DEMO_PHARMACY_RATES: dict[str, float] = {
	f"{DEMO_MARKER}{code}": rate for code, _, rate in PHARMACY_ITEMS
}


def _item_has_field(fieldname: str) -> bool:
	return bool(frappe.get_meta("Item").has_field(fieldname))


def _demo_pharmacy_item_rate(item_code: str, fallback: float = 10.0) -> float:
	return _DEMO_PHARMACY_RATES.get(item_code, fallback)


def _resolve_item_name(item_code: str, company: str) -> str | None:
	return frappe.db.get_value("Item", {"item_code": item_code, "company": company}, "name")


def _stock_entry_item_row(item_name: str, warehouse: str, qty: float, rate: float) -> dict:
	item_code = frappe.db.get_value("Item", item_name, "item_code")
	uom = frappe.db.get_value("Item", item_name, "stock_uom") or "Nos"
	row: dict = {
		"item": item_name,
		"item_code": item_code,
		"qty": qty,
		"t_warehouse": warehouse,
		"uom": uom,
	}
	item_meta = frappe.get_meta("Stock Entry Item")
	if item_meta.has_field("rate"):
		row["rate"] = rate
	elif item_meta.has_field("basic_rate"):
		row["basic_rate"] = rate
	return row


def _invoice_item_row(item_name: str, qty: float, rate: float) -> dict:
	item_code = frappe.db.get_value("Item", item_name, "item_code")
	return {"item": item_name, "item_code": item_code, "qty": qty, "rate": rate}


def _service_charge_line(item_name: str, description: str, qty: float, rate: float) -> dict:
	item_code = frappe.db.get_value("Item", item_name, "item_code")
	return {
		"item": item_name,
		"item_code": item_code,
		"description": description,
		"qty": qty,
		"rate": rate,
	}

ICD10_SAMPLES = [
	("I10", "Essential hypertension"),
	("E11.9", "Type 2 diabetes mellitus"),
	("J06.9", "Acute upper respiratory infection"),
	("M54.5", "Low back pain"),
	("K21.9", "Gastro-esophageal reflux disease"),
]

WEB_SERVICES: list[tuple[str, str, str, str, float, str]] = [
	("CONS-GEN", "General Medicine Consultation", "GEN", "OPD", 350.0, "استشارة طب عام — حجز عبر الموقع"),
	("CONS-CARD", "Cardiology Consultation", "CAR", "CARD", 500.0, "استشارة قلب — حجز عبر الموقع"),
	("CONS-PED", "Pediatrics Consultation", "PED", "PED", 300.0, "عيادة أطفال — حجز عبر الموقع"),
	("CONS-ORT", "Orthopedics Consultation", "ORT", "ORT", 400.0, "عظام ومفاصل — حجز عبر الموقع"),
	("CONS-DER", "Dermatology Consultation", "DER", "DER", 350.0, "جلدية — حجز عبر الموقع"),
	("CONS-DEN", "Dental Consultation", "DEN", "DEN", 400.0, "عيادة أسنان — حجز عبر الموقع"),
	("CONS-ENT", "ENT Consultation", "ENT", "OPD", 380.0, "أنف وأذن وحنجرة — حجز عبر الموقع"),
	("CONS-GYN", "Gynecology Consultation", "GYN", "OPD", 420.0, "نساء وولادة — حجز عبر الموقع"),
	("PKG-DENTAL", "Dental Checkup Package", "DEN", "DEN", 500.0, "باقة فحص وتنظيف أسنان"),
	("LAB-CBC", "CBC Laboratory Panel", "LAB", "LAB", 250.0, "تحليل صورة دم كاملة"),
	("RAD-CXR", "Chest X-Ray", "RAD", "RAD", 450.0, "أشعة صدر"),
	("TEL-FU", "Telehealth Follow-up", "GEN", "OPD", 200.0, "متابعة عن بُعد"),
]

WEB_BOOKING_STATUSES: list[tuple[str, str, int]] = [
	("Scheduled", "Paid", 5),
	("Scheduled", "Unpaid", 4),
	("Scheduled", "Paid", 7),
	("Scheduled", "Unpaid", 10),
	("Arrived", "Paid", 0),
	("In Consultation", "Paid", 0),
	("Cancelled", "Unpaid", -2),
	("No Show", "Unpaid", -3),
	("Completed", "Paid", -1),
	("Completed", "Paid", -4),
	("Scheduled", "Partially Paid", 14),
	("Scheduled", "Unpaid", 21),
]


def seed_healthcare_hospital_demo(
	company: str,
	branch: str,
	patients: int = 20,
	force: int = 0,
	include_financial: int = 1,
) -> dict:
	"""Seed a full multi-specialty hospital demo for one branch."""
	if not company or not branch:
		frappe.throw(_("Company and branch are required"))
	if frappe.db.get_value("Branch", branch, "company") != company:
		frappe.throw(_("Branch does not belong to company"))

	patient_count = max(1, min(50, cint(patients) or 20))
	facility_key = f"{company}-{branch}-Hospital"
	if cint(force):
		reset_healthcare_demo_for_branch(company, branch, dry_run=0)
	elif frappe.db.exists("Healthcare Facility Profile", facility_key):
		demo_patients = _count_demo_patients(company, branch)
		published = frappe.db.count(
			"Healthcare Service Catalog",
			{"company": company, "branch": branch, "publish_on_website": 1},
		)
		web_bookings = frappe.db.count(
			"Healthcare Appointment",
			{"company": company, "branch": branch, "booking_channel": "Website"},
		)
		return {
			"ok": True,
			"message": "already_seeded",
			"facility": facility_key,
			"patients": demo_patients,
			"published_services": published,
			"web_bookings": web_bookings,
			"web_booking_url": f"/healthcare-booking?company={quote(company)}&branch={quote(branch)}",
			"hint": _("Demo already exists ({0} patients). Enable Rebuild demo and click again to recreate.").format(
				demo_patients
			),
		}

	seeder = _HospitalDemoSeeder(
		company=company,
		branch=branch,
		patient_count=patient_count,
		include_financial=cint(include_financial),
	)
	return seeder.run()


def _count_demo_patients(company: str, branch: str) -> int:
	patient_names = frappe.get_all(
		"Healthcare Patient Identifier",
		filters={"value": ["like", f"{DEMO_MARKER}%"], "parenttype": "Healthcare Patient"},
		pluck="parent",
	)
	return len({p for p in patient_names if frappe.db.get_value("Healthcare Patient", p, "branch") == branch})


def reset_healthcare_demo_for_branch(company: str, branch: str, dry_run: int = 0) -> dict:
	"""Remove DEMO-HC healthcare records for a branch."""
	stats: dict[str, int] = {}
	patient_names = frappe.get_all(
		"Healthcare Patient Identifier",
		filters={"value": ["like", f"{DEMO_MARKER}%"], "parenttype": "Healthcare Patient"},
		pluck="parent",
	)
	patients = list(set(patient_names))
	filters_base = {"company": company, "branch": branch}

	delete_order = [
		"Healthcare Follow Up Plan",
		"Healthcare Orthodontic Case",
		"Healthcare Dental Treatment Plan",
		"Healthcare Dental Chart Entry",
		"Healthcare Installment Plan",
		"Healthcare Treatment Package",
		"Healthcare Service Catalog",
		"Healthcare Service Charge",
		"Healthcare Medication Dispense",
		"Healthcare Ward Requisition",
		"Healthcare Diagnostic Report",
		"Healthcare Lab Sample",
		"Healthcare Service Request",
		"Healthcare Observation",
		"Healthcare Medication Statement",
		"Healthcare Clinical Condition",
		"Healthcare Allergy Intolerance",
		"Healthcare Er Visit",
		"Healthcare Critical Care Monitoring",
		"Healthcare Companion Stay",
		"Healthcare Admission",
		"Healthcare Encounter",
		"Healthcare Appointment",
		"Healthcare Episode Of Care",
		"Healthcare Patient",
		"Healthcare Practitioner",
		"Healthcare Bed",
		"Healthcare Service Unit",
		"Healthcare Department",
		"Healthcare Facility Profile",
		"Healthcare Item Par Level",
		"Healthcare Payer",
	]

	for dt in delete_order:
		names: list[str] = []
		if dt == "Healthcare Patient" and patients:
			names = [p for p in patients if frappe.db.get_value(dt, p, "branch") == branch]
		elif dt == "Healthcare Facility Profile":
			names = frappe.get_all(dt, filters={**filters_base, "facility_name": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
		else:
			extra = {}
			if frappe.get_meta(dt).has_field("patient") and patients:
				names = frappe.get_all(dt, filters={**filters_base, "patient": ["in", patients]}, pluck="name")
			else:
				if frappe.get_meta(dt).has_field("reporting_tag"):
					extra["reporting_tag"] = REPORTING_TAG
				if frappe.get_meta(dt).has_field("practitioner_name"):
					names = frappe.get_all(dt, filters={**filters_base, "practitioner_name": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif frappe.get_meta(dt).has_field("unit_code"):
					names = frappe.get_all(dt, filters={**filters_base, "unit_code": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif frappe.get_meta(dt).has_field("department_code"):
					names = frappe.get_all(dt, filters={**filters_base, "department_code": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif dt == "Healthcare Service Catalog":
					names = frappe.get_all(dt, filters={**filters_base, "service_code": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif dt == "Healthcare Treatment Package":
					names = frappe.get_all(dt, filters={"package_code": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif dt == "Healthcare Payer":
					names = frappe.get_all(dt, filters={"company": company, "payer_code": ["like", f"{DEMO_MARKER}%"]}, pluck="name")
				elif extra:
					names = frappe.get_all(dt, filters={**filters_base, **extra}, pluck="name")
		count = len(names)
		stats[dt] = count
		if dry_run or not names:
			continue
		for name in names:
			try:
				frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"DEMO-HC reset failed: {dt} {name}")

	if not dry_run:
		for page in frappe.get_all("Web Page", filters={"title": ["like", f"{DEMO_MARKER}%"]}, pluck="name"):
			try:
				frappe.delete_doc("Web Page", page, force=1, ignore_permissions=True)
			except Exception:
				pass
		for item_code in [f"{DEMO_MARKER}{c}" for c, _, _ in PHARMACY_ITEMS]:
			if frappe.db.exists("Item", {"item_code": item_code, "company": company}):
				try:
					frappe.delete_doc("Item", item_code, force=1, ignore_permissions=True)
				except Exception:
					pass
		frappe.db.commit()

	return {"ok": True, "dry_run": bool(dry_run), "deleted": stats, "patients": len(patients)}


class _HospitalDemoSeeder:
	def __init__(self, company: str, branch: str, patient_count: int, include_financial: int):
		self.company = company
		self.branch = branch
		self.patient_count = patient_count
		self.include_financial = include_financial
		self.stats: dict[str, int] = {}
		self.ctx: dict = {}

	def run(self) -> dict:
		frappe.set_user("Administrator")
		self._ensure_uom()
		self._ensure_country()
		self._seed_masters()
		if self.patient_count:
			self._seed_patients_and_journeys()
			self._seed_critical_care_demo()
			self._seed_specialty_excellence()
		self._seed_website_services_and_bookings()
		if self.include_financial:
			self._seed_inventory_and_finance()
		frappe.db.commit()
		return {
			"ok": True,
			"message": "healthcare_hospital_demo_seeded",
			"company": self.company,
			"branch": self.branch,
			"patients": len(self.ctx.get("patients") or []) or self.patient_count,
			"stats": self.stats,
			"facility": self.ctx.get("facility"),
			"web_booking_url": self.ctx.get("web_booking_url"),
			"hospital_site_url": self.ctx.get("hospital_site_url"),
			"published_services": len(self.ctx.get("published_services") or []),
			"web_bookings": self.stats.get("Healthcare Appointment (Website)", 0),
			"specialty_modules": self.ctx.get("specialty_modules_count", 0),
			"dental_charts": self.stats.get("Healthcare Dental Chart Entry", 0),
			"treatment_plans": self.stats.get("Healthcare Dental Treatment Plan", 0),
			"follow_up_plans": self.stats.get("Healthcare Follow Up Plan", 0),
		}

	def _bump(self, key: str, n: int = 1) -> None:
		self.stats[key] = self.stats.get(key, 0) + n

	def _ensure_uom(self) -> None:
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)
		if not frappe.db.exists("UOM", "Box"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Box"}).insert(ignore_permissions=True)

	def _ensure_country(self, country: str = "Egypt") -> None:
		if not frappe.db.exists("Country", country):
			frappe.get_doc({"doctype": "Country", "country_name": country, "code": "EG"}).insert(
				ignore_permissions=True
			)

	def _insert(self, doctype: str, data: dict):
		doc = frappe.get_doc({"doctype": doctype, **data})
		doc.insert(ignore_permissions=True)
		self._bump(doctype)
		return doc

	def _demo_billing_item(self) -> str:
		"""Service item for OPD billing demo (Sales Invoice + Service Charge lines)."""
		cached = self.ctx.get("billing_item")
		if cached and frappe.db.exists("Item", cached):
			return cached
		item_code = f"{DEMO_MARKER}OPD-SVC"
		existing = _resolve_item_name(item_code, self.company)
		if existing:
			self.ctx["billing_item"] = existing
			return existing
		payload: dict = {
			"item_code": item_code,
			"item_name": f"{DEMO_MARKER} OPD Consultation Service",
			"company": self.company,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
		}
		if _item_has_field("product_type"):
			payload["product_type"] = "Service"
		item = self._insert("Item", payload)
		self.ctx["billing_item"] = item.name
		return item.name

	def _seed_masters(self) -> None:
		for code, desc in ICD10_SAMPLES:
			if not frappe.db.exists("Healthcare Icd10 Code", {"code": code}):
				self._insert("Healthcare Icd10 Code", {"code": code, "description": desc, "is_active": 1})

		facility_name = f"{DEMO_MARKER} Multi-Specialty Hospital"
		facility = self._insert(
			"Healthcare Facility Profile",
			{
				"facility_name": facility_name,
				"company": self.company,
				"branch": self.branch,
				"facility_type": "Hospital",
				"status": "Active",
			},
		)
		self.ctx["facility"] = facility.name

		from omnexa_healthcare.specialty_engine import seed_default_specialty_modules

		seed_default_specialty_modules(company=self.company)
		self.ctx["specialty_modules_count"] = frappe.db.count("Healthcare Specialty Module", {"is_active": 1})

		depts: dict[str, str] = {}
		units: dict[str, str] = {}
		for code, label, unit_type in DEPARTMENTS:
			dept_code = f"{DEMO_MARKER}{code}"
			dept = self._insert(
				"Healthcare Department",
				{
					"department_name": f"{DEMO_MARKER} {label}",
					"department_code": dept_code,
					"company": self.company,
					"branch": self.branch,
					"status": "Active",
				},
			)
			depts[code] = dept.name
			unit = self._insert(
				"Healthcare Service Unit",
				{
					"unit_name": f"{DEMO_MARKER} {label} Unit",
					"unit_code": dept_code,
					"company": self.company,
					"branch": self.branch,
					"department": dept.name,
					"unit_type": unit_type,
					"status": "Active",
				},
			)
			units[code] = unit.name

		self.ctx["departments"] = depts
		self.ctx["units"] = units

		beds: list[str] = []
		for i in range(1, 11):
			bed = self._insert(
				"Healthcare Bed",
				{
					"bed_label": f"{DEMO_MARKER} Bed {i:02d}",
					"company": self.company,
					"branch": self.branch,
					"service_unit": units["IPD"],
					"status": "Available" if i > 4 else "Occupied",
				},
			)
			beds.append(bed.name)
		self.ctx["beds"] = beds

		critical_beds: dict[str, str] = {}
		for label, unit_key, bed_type in (
			("ICU-01", "ICU", "ICU"),
			("ICU-02", "ICU", "HDU"),
			("NICU-01", "NICU", "NICU"),
			("Nursery-01", "NICU", "Nursery"),
			("CMP-01", "CMP", "Companion"),
			("CMP-02", "CMP", "Companion"),
		):
			b = self._insert(
				"Healthcare Bed",
				{
					"bed_label": f"{DEMO_MARKER} {label}",
					"company": self.company,
					"branch": self.branch,
					"service_unit": units[unit_key],
					"bed_type": bed_type,
					"status": "Available",
				},
			)
			critical_beds[label] = b.name
		self.ctx["critical_beds"] = critical_beds

		practitioners: dict[str, str] = {}
		unit_map = {
			"GEN": "OPD",
			"CAR": "CARD",
			"PED": "PED",
			"ORT": "ORT",
			"DER": "DER",
			"DEN": "DEN",
			"ENT": "OPD",
			"GYN": "OPD",
			"RAD": "RAD",
			"LAB": "LAB",
		}
		for spec, name, label in PRACTITIONERS:
			specialty_link = self._resolve_specialty(label, spec)
			unit_key = unit_map.get(spec, "OPD")
			schedule = [
				{
					"branch": self.branch,
					"day_of_week": day,
					"from_time": "09:00:00",
					"to_time": "17:00:00",
					"slot_duration_mins": 30,
					"specialty": specialty_link,
				}
				for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
			]
			pr = self._insert(
				"Healthcare Practitioner",
				{
					"practitioner_name": f"{DEMO_MARKER} {name}",
					"company": self.company,
					"status": "Active",
					"license_number": f"LIC-{spec}-001",
					"branch_assignments": [
						{
							"branch": self.branch,
							"facility_profile": facility.name,
							"service_unit": units.get(unit_key),
							"specialty": specialty_link,
							"consultation_fee": 350,
							"is_active": 1,
						}
					],
					"schedule": schedule,
				},
			)
			practitioners[spec] = pr.name
		self.ctx["practitioners"] = practitioners

		payer_code = f"{DEMO_MARKER}INS"
		if not frappe.db.exists("Healthcare Payer", payer_code):
			payer = self._insert(
				"Healthcare Payer",
				{
					"payer_name": f"{DEMO_MARKER} National Insurance",
					"payer_code": payer_code,
					"company": self.company,
					"payer_type": "Insurance",
					"is_active": 1,
				},
			)
			self.ctx["payer"] = payer.name

	def _seed_patients_and_journeys(self) -> None:
		depts = self.ctx["departments"]
		units = self.ctx["units"]
		practitioners = self.ctx["practitioners"]
		facility = self.ctx["facility"]
		clinic_rotation = CLINIC_ROTATION
		patients: list[str] = []

		for idx, (given, family, gender, birth_year) in enumerate(PATIENT_ROSTER[: self.patient_count]):
			mrn = f"{DEMO_MARKER}MRN-{idx + 1:03d}"
			national_id = f"{29000000000000 + idx}"
			identifiers = [
				{
					"identifier_use": "official",
					"identifier_type": "MRN",
					"value": mrn,
					"is_primary_mrn": 1,
				}
			]
			if idx % 2 == 0:
				identifiers.append(
					{
						"identifier_use": "official",
						"identifier_type": "National ID",
						"value": national_id,
						"is_primary_mrn": 0,
					}
				)

			patient = self._insert(
				"Healthcare Patient",
				{
					"naming_series": "HP-.#####",
					"company": self.company,
					"branch": self.branch,
					"managing_facility": facility,
					"given_name": given,
					"family_name": family,
					"gender": gender,
					"birth_date": f"{birth_year}-06-15",
					"birth_date_precision": "DMY",
					"nationality": "Egypt",
					"preferred_language": "ar",
					"communication_language": "ar",
					"marital_status": ["S", "M", "D", "W"][idx % 4],
					"blood_group": ["A+", "B+", "O+", "AB+"][idx % 4],
					"address_use": "home",
					"address_type": "physical",
					"address_line1": f"{12 + idx} Nile Corniche",
					"city": "Cairo",
					"district": "Nasr City",
					"state": "Cairo",
					"postal_code": f"113{idx:02d}",
					"country": "Egypt",
					"consent_to_care_recorded_at": now_datetime(),
					"consent_notes": "Demo consent for care and billing (FHIR Patient consent).",
					"identifiers": identifiers,
					"telecom": [
						{"contact_system": "phone", "contact_use": "mobile", "value": f"+2010{idx:08d}", "rank": 1},
						{
							"contact_system": "email",
							"contact_use": "home",
							"value": f"{given.lower()}.{family.lower()}@demo.health",
							"rank": 2,
						},
					],
				},
			)
			patients.append(patient.name)

			if idx % 3 == 0:
				self._insert(
					"Healthcare Clinical Condition",
					{
						"naming_series": "CC-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"category": "problem-list-item",
						"icd10_code": ICD10_SAMPLES[idx % len(ICD10_SAMPLES)][0],
						"clinical_description": ICD10_SAMPLES[idx % len(ICD10_SAMPLES)][1],
						"clinical_status": "active",
						"verification_status": "confirmed",
					},
				)
			if idx % 5 == 0:
				self._insert(
					"Healthcare Allergy Intolerance",
					{
						"naming_series": "ALG-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"allergy_type": "allergy",
						"category": "medication",
						"criticality": "low",
						"substance_text": "Penicillin",
						"clinical_status": "active",
						"verification_status": "confirmed",
					},
				)

			clinic, pr_spec, _spec_label = clinic_rotation[idx % len(clinic_rotation)]
			specialty_link = self._resolve_specialty(_spec_label, pr_spec)
			appt_date = add_days(today(), -(idx % 14) + 3)
			appt = self._insert(
				"Healthcare Appointment",
				{
					"naming_series": "HAP-.#####",
					"patient": patient.name,
					"company": self.company,
					"branch": self.branch,
					"department": depts[clinic],
					"service_unit": units[clinic],
					"practitioner": practitioners[pr_spec],
					"specialty": specialty_link,
					"appointment_date": f"{appt_date} {(9 + idx % 6):02d}:00:00",
					"appointment_type": "Follow-up" if idx % 2 else "Consultation",
					"status": "Completed" if getdate(appt_date) < getdate(today()) else "Scheduled",
				},
			)

			if getdate(appt_date) <= getdate(today()):
				enc = self._insert(
					"Healthcare Encounter",
					{
						"naming_series": "ENC-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"encounter_class": "ambulatory",
						"encounter_type": "OPD",
						"status": "finished",
						"period_start": f"{appt_date} {(9 + idx % 6):02d}:00:00",
						"period_end": f"{appt_date} {(9 + idx % 6):02d}:30:00",
						"department": depts[clinic],
						"service_unit": units[clinic],
						"practitioner": practitioners[pr_spec],
					},
				)
				frappe.db.set_value("Healthcare Appointment", appt.name, "encounter", enc.name)

				if idx % 2 == 0:
					srq = self._insert(
						"Healthcare Service Request",
						{
							"naming_series": "SRQ-.#####",
							"patient": patient.name,
							"company": self.company,
							"branch": self.branch,
							"encounter": enc.name,
							"status": "completed",
							"intent": "order",
							"request_category": "laboratory",
							"request_title": "CBC + Chemistry Panel",
							"priority": "routine",
							"authored_on": f"{appt_date} {(10 + idx % 5):02d}:15:00",
						},
					)
					sample = self._insert(
						"Healthcare Lab Sample",
						{
							"naming_series": "LSP-.#####",
							"patient": patient.name,
							"company": self.company,
							"branch": self.branch,
							"service_request": srq.name,
							"specimen_id": f"{DEMO_MARKER}SMP-{idx + 1:03d}",
							"collected_datetime": f"{appt_date} {(10 + idx % 5):02d}:30:00",
							"status": "completed",
							"sample_type": "Blood",
						},
					)
					self._insert(
						"Healthcare Diagnostic Report",
						{
							"naming_series": "DGR-.#####",
							"patient": patient.name,
							"company": self.company,
							"branch": self.branch,
							"based_on_service_request": srq.name,
							"status": "final",
							"report_category": "laboratory",
							"report_title": "CBC + Chemistry Panel",
							"conclusion": "Within normal limits (demo).",
							"effective_datetime": f"{appt_date} {(11 + idx % 4):02d}:00:00",
						},
					)

				if idx % 3 == 0:
					modality = frappe.db.get_value("Healthcare Imaging Modality", {"modality_code": "XR"}, "name")
					rad_data = {
						"naming_series": "SRQ-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"encounter": enc.name,
						"status": "completed",
						"intent": "order",
						"request_category": "imaging",
						"request_title": "Chest X-Ray",
						"priority": "routine",
						"authored_on": f"{appt_date} {(11 + idx % 3):02d}:00:00",
					}
					if modality:
						rad_data["modality"] = modality
					rad_req = self._insert("Healthcare Service Request", rad_data)
					self._insert(
						"Healthcare Diagnostic Report",
						{
							"naming_series": "DGR-.#####",
							"patient": patient.name,
							"company": self.company,
							"branch": self.branch,
							"based_on_service_request": rad_req.name,
							"status": "final",
							"report_category": "radiology",
							"report_title": "Chest X-Ray",
							"conclusion": "No acute cardiopulmonary abnormality (demo).",
							"effective_datetime": f"{appt_date} {(12 + idx % 3):02d}:00:00",
						},
					)

				self._insert(
					"Healthcare Observation",
					{
						"naming_series": "OBS-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"encounter": enc.name,
						"status": "final",
						"category": "vital-signs",
						"observation_profile": "blood_pressure",
						"value_primary": 118 + (idx % 15),
						"value_secondary": 72 + (idx % 8),
						"unit_ucum": "mm[Hg]",
						"effective_datetime": f"{appt_date} {(9 + idx % 6):02d}:05:00",
					},
				)

				if idx % 4 == 0:
					self._insert(
						"Healthcare Medication Statement",
						{
							"naming_series": "MED-.#####",
							"patient": patient.name,
							"company": self.company,
							"branch": self.branch,
							"encounter": enc.name,
							"status": "active",
							"medication_text": "Metformin 500 mg BD",
							"dosage_text": "With meals",
							"category": "community",
						},
					)

			if idx % 6 == 0:
				self._insert(
					"Healthcare Er Visit",
					{
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"esi_level": str((idx % 4) + 1),
						"chief_complaint": "Acute abdominal pain (demo)",
						"status": "Completed",
						"disposition": "Discharge",
						"arrival_datetime": f"{add_days(today(), -2)} 14:30:00",
					},
				)

			if idx % 7 == 0 and self.ctx.get("beds"):
				self._insert(
					"Healthcare Admission",
					{
						"naming_series": "ADM-.#####",
						"patient": patient.name,
						"company": self.company,
						"branch": self.branch,
						"admission_class": "elective",
						"status": "admitted" if idx % 14 != 0 else "discharged",
						"bed": self.ctx["beds"][idx % len(self.ctx["beds"])],
						"admission_datetime": f"{add_days(today(), -5)} 08:00:00",
						"expected_discharge_date": add_days(today(), 2),
					},
				)

		self.ctx["patients"] = patients

	def _seed_critical_care_demo(self) -> None:
		patients = self.ctx.get("patients") or []
		beds = self.ctx.get("critical_beds") or {}
		if len(patients) < 6 or not beds:
			return
		icu_admit = self._insert(
			"Healthcare Admission",
			{
				"naming_series": "ADM-.#####",
				"patient": patients[3],
				"company": self.company,
				"branch": self.branch,
				"admission_class": "emergency",
				"status": "admitted",
				"bed": beds["ICU-01"],
				"admission_datetime": f"{add_days(today(), -1)} 09:00:00",
			},
		)
		nicu_admit = self._insert(
			"Healthcare Admission",
			{
				"naming_series": "ADM-.#####",
				"patient": patients[4],
				"company": self.company,
				"branch": self.branch,
				"admission_class": "emergency",
				"status": "admitted",
				"bed": beds["NICU-01"],
				"admission_datetime": f"{add_days(today(), -2)} 11:30:00",
			},
		)
		self._insert(
			"Healthcare Critical Care Monitoring",
			{
				"patient": patients[3],
				"admission": icu_admit.name,
				"bed": beds["ICU-01"],
				"care_unit": "ICU",
				"recorded_at": now_datetime(),
				"heart_rate": 98,
				"respiratory_rate": 18,
				"spo2": 96.0,
				"bp_systolic": 128,
				"bp_diastolic": 78,
				"temperature_c": 37.1,
				"fio2_percent": 40.0,
				"company": self.company,
				"branch": self.branch,
			},
		)
		self._insert(
			"Healthcare Critical Care Monitoring",
			{
				"patient": patients[4],
				"admission": nicu_admit.name,
				"bed": beds["NICU-01"],
				"care_unit": "NICU",
				"recorded_at": now_datetime(),
				"heart_rate": 142,
				"respiratory_rate": 42,
				"spo2": 91.0,
				"temperature_c": 36.8,
				"weight_g": 2100.0,
				"gestational_age_weeks": 34.0,
				"company": self.company,
				"branch": self.branch,
			},
		)
		ipd_beds = self.ctx.get("beds") or []
		if ipd_beds:
			ipd_admit = self._insert(
				"Healthcare Admission",
				{
					"naming_series": "ADM-.#####",
					"patient": patients[5],
					"company": self.company,
					"branch": self.branch,
					"admission_class": "elective",
					"status": "admitted",
					"bed": ipd_beds[8],
					"admission_datetime": f"{add_days(today(), -3)} 10:00:00",
				},
			)
			self._insert(
				"Healthcare Companion Stay",
				{
					"patient": patients[5],
					"admission": ipd_admit.name,
					"companion_name": "Ahmed Hassan (demo escort)",
					"relationship": "Father",
					"bed": beds["CMP-01"],
					"check_in_datetime": f"{add_days(today(), -1)} 18:00:00",
					"status": "active",
					"company": self.company,
					"branch": self.branch,
				},
			)

	def _resolve_specialty(self, label: str, fallback_code: str | None = None) -> str:
		code = frappe.db.get_value("Healthcare Specialty", {"specialty_name": label})
		if code:
			return code
		if fallback_code and frappe.db.exists("Healthcare Specialty", fallback_code):
			return fallback_code
		doc = self._insert(
			"Healthcare Specialty",
			{"specialty_code": fallback_code or label[:12].upper().replace(" ", ""), "specialty_name": label, "is_active": 1},
		)
		return doc.name

	def _seed_specialty_excellence(self) -> None:
		"""Dental charts, treatment plans, ortho, packages, installments — all 15 specialty modules."""
		practitioners = self.ctx.get("practitioners") or {}
		patients = self.ctx.get("patients") or []
		dental_pr = practitioners.get("DEN") or practitioners.get("GEN")
		dental_spec = self._resolve_specialty("Dental", "DEN")

		for package_code, package_name, spec_label, total_price, items in TREATMENT_PACKAGES:
			if frappe.db.exists("Healthcare Treatment Package", package_code):
				continue
			spec_link = self._resolve_specialty(spec_label, SPECIALTY_LABEL_BY_CODE.get(spec_label, spec_label[:3].upper()))
			billing_item = self._demo_billing_item()
			self._insert(
				"Healthcare Treatment Package",
				{
					"package_code": package_code,
					"package_name": package_name,
					"specialty": spec_link,
					"total_price": total_price,
					"company": self.company,
					"is_active": 1,
					"items": [
						{
							"item_code": billing_item,
							"procedure": proc,
							"qty": 1,
							"rate": rate,
							"amount": rate,
						}
						for proc, rate in items
					],
				},
			)

		for idx, patient in enumerate(patients):
			encounter = frappe.db.get_value(
				"Healthcare Encounter",
				{"patient": patient, "company": self.company, "branch": self.branch},
				"name",
				order_by="modified desc",
			)

			if idx % 3 == 0 and dental_pr:
				for tooth_id, surface, condition in DENTAL_DEMO_TEETH[:3 if idx % 6 else 5]:
					self._insert(
						"Healthcare Dental Chart Entry",
						{
							"patient": patient,
							"encounter": encounter,
							"practitioner": dental_pr,
							"company": self.company,
							"branch": self.branch,
							"tooth_numbering_system": "FDI",
							"tooth_id": tooth_id,
							"surface": surface,
							"condition": condition,
							"status": "completed" if condition in ("filled", "crown") else "planned",
							"treatment_plan": f"{DEMO_MARKER} demo charting",
						},
					)

			if idx % 4 == 0 and dental_pr:
				plan = self._insert(
					"Healthcare Dental Treatment Plan",
					{
						"patient": patient,
						"plan_title": f"{DEMO_MARKER} Multi-visit restorative plan",
						"practitioner": dental_pr,
						"specialty": dental_spec,
						"company": self.company,
						"branch": self.branch,
						"status": "active",
						"visits": [
							{"visit_no": 1, "planned_date": add_days(today(), 7), "procedure": "Exam + X-ray", "tooth_id": "11", "status": "completed"},
							{"visit_no": 2, "planned_date": add_days(today(), 14), "procedure": "Composite filling", "tooth_id": "11", "status": "planned"},
							{"visit_no": 3, "planned_date": add_days(today(), 28), "procedure": "Crown prep", "tooth_id": "26", "status": "planned"},
						],
					},
				)
				if idx % 8 == 0:
					self._insert(
						"Healthcare Orthodontic Case",
						{
							"patient": patient,
							"dental_treatment_plan": plan.name,
							"appliance_type": "Metal Braces" if idx % 16 == 0 else "Clear Aligners",
							"start_date": add_days(today(), -30),
							"estimated_months": 18,
							"company": self.company,
							"branch": self.branch,
							"status": "active",
							"notes": f"{DEMO_MARKER} ortho demo case",
						},
					)

			if idx % 6 == 0 and self.include_financial:
				total = 6000.0 if idx % 12 == 0 else 3000.0
				count = 6 if idx % 12 == 0 else 3
				per = round(total / count, 2)
				self._insert(
					"Healthcare Installment Plan",
					{
						"patient": patient,
						"total_amount": total,
						"installment_count": count,
						"frequency": "Monthly",
						"company": self.company,
						"branch": self.branch,
						"status": "active",
						"installments": [
							{
								"installment_no": n + 1,
								"due_date": add_days(today(), 30 * (n + 1)),
								"amount": per,
								"paid": 1 if n == 0 else 0,
							}
							for n in range(count)
						],
					},
				)

		self._seed_multi_visit_follow_up_plans(patients, practitioners)

	def _seed_multi_visit_follow_up_plans(self, patients: list[str], practitioners: dict[str, str]) -> None:
		from omnexa_healthcare.api.follow_up_plan import create_follow_up_plan

		for patient_idx, module_code, plan_type, pr_key in DEMO_FOLLOW_UP_ASSIGNMENTS:
			if patient_idx >= len(patients):
				continue
			patient = patients[patient_idx]
			specialty = frappe.db.get_value("Healthcare Specialty Module", module_code, "specialty")
			if not specialty:
				continue
			existing = frappe.db.exists(
				"Healthcare Follow Up Plan",
				{"patient": patient, "specialty": specialty, "plan_type": plan_type, "plan_title": ["like", f"%{DEMO_MARKER}%"]},
			)
			if existing:
				continue
			try:
				out = create_follow_up_plan(
					patient=patient,
					specialty=specialty,
					plan_type=plan_type,
					plan_title=f"{DEMO_MARKER} {module_code.replace('_', ' ').title()} follow-up",
					practitioner=practitioners.get(pr_key),
					company=self.company,
					branch=self.branch,
					start_date=add_days(today(), -(patient_idx % 5) * 7),
				)
				plan_name = out.get("name")
				if plan_name and patient_idx % 3 == 0:
					plan_doc = frappe.get_doc("Healthcare Follow Up Plan", plan_name)
					if plan_doc.visits:
						plan_doc.visits[0].status = "completed"
						plan_doc.save(ignore_permissions=True)
				self._bump("Healthcare Follow Up Plan")
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"DEMO-HC follow-up plan {module_code} patient {patient_idx}")

	def _seed_website_services_and_bookings(self) -> None:
		depts = self.ctx.get("departments") or {}
		units = self.ctx.get("units") or {}
		practitioners = self.ctx.get("practitioners") or {}
		patients = self.ctx.get("patients") or []
		published: list[str] = []

		for order, (code, title, spec, dept_key, rate, desc) in enumerate(WEB_SERVICES, start=1):
			service_code = f"{DEMO_MARKER}{code}"
			if frappe.db.exists("Healthcare Service Catalog", service_code):
				published.append(service_code)
				continue
			service_type = "Telehealth" if code.startswith("TEL") else ("Procedure" if dept_key in ("LAB", "RAD") else "Consultation")
			spec_label = SPECIALTY_LABEL_BY_CODE.get(spec, spec)
			specialty_link = self._resolve_specialty(spec_label, spec)
			self._insert(
				"Healthcare Service Catalog",
				{
					"service_code": service_code,
					"service_title": f"{DEMO_MARKER} {title}",
					"specialty": specialty_link,
					"service_type": service_type,
					"default_rate": rate,
					"duration_mins": 30,
					"company": self.company,
					"branch": self.branch,
					"department": depts.get(dept_key),
					"default_practitioner": practitioners.get(spec),
					"publish_on_website": 1,
					"display_order": order * 10,
					"website_description": desc,
					"is_active": 1,
				},
			)
			published.append(service_code)

		self.ctx["published_services"] = published
		self._seed_branch_public_website()
		booking_url = f"/healthcare-booking?company={quote(self.company)}&branch={quote(self.branch)}"
		self.ctx["web_booking_url"] = booking_url

		page_title = f"{DEMO_MARKER} Hospital Online Booking"
		if not frappe.db.exists("Web Page", {"title": page_title}):
			self._insert(
				"Web Page",
				{
					"title": page_title,
					"route": f"hospital-booking-{self.branch.lower().replace(' ', '-')[:40]}",
					"published": 1,
					"content_type": "Rich Text",
					"main_section": (
						f"<h3>حجز مواعيد المستشفى</h3>"
						f"<p>احجز خدمات العيادات والتحاليل والأشعة عبر الإنترنت.</p>"
						f'<p><a class="btn btn-primary" href="{booking_url}">افتح صفحة الحجز / Open booking page</a></p>'
					),
				},
			)

		clinic_specs = [row[1] for row in CLINIC_ROTATION]
		clinic_dept_map = {row[1]: row[0] for row in CLINIC_ROTATION}
		clinic_label_map = {row[1]: row[2] for row in CLINIC_ROTATION}
		for idx, (status, payment_status, day_offset) in enumerate(WEB_BOOKING_STATUSES):
			if idx >= len(patients):
				break
			patient = patients[idx]
			spec = clinic_specs[idx % len(clinic_specs)]
			dept_key = clinic_dept_map[spec]
			specialty_link = self._resolve_specialty(clinic_label_map[spec], spec)
			appt_day = add_days(today(), day_offset)
			hour = 10 + (idx % 5)
			start = f"{appt_day} {hour:02d}:00:00"
			end = f"{appt_day} {hour:02d}:30:00"
			service = published[idx % len(published)] if published else None
			rate = frappe.db.get_value("Healthcare Service Catalog", service, "default_rate") if service else 350
			appt = self._insert(
				"Healthcare Appointment",
				{
					"naming_series": "HAP-.#####",
					"patient": patient,
					"company": self.company,
					"branch": self.branch,
					"department": depts[dept_key],
					"service_unit": units[dept_key],
					"practitioner": practitioners[spec],
					"specialty": specialty_link,
					"appointment_date": start,
					"slot_end": end,
					"appointment_type": "Consultation",
					"status": status,
					"booking_fee": flt(rate),
					"payment_status": payment_status,
					"booking_channel": "Website",
				},
			)
			self._bump("Healthcare Appointment (Website)")
			if status == "Completed" and getdate(appt_day) <= getdate(today()):
				enc = self._insert(
					"Healthcare Encounter",
					{
						"naming_series": "ENC-.#####",
						"patient": patient,
						"company": self.company,
						"branch": self.branch,
						"encounter_class": "ambulatory",
						"encounter_type": "OPD",
						"status": "finished",
						"period_start": start,
						"period_end": end,
						"department": depts[dept_key],
						"service_unit": units[dept_key],
						"practitioner": practitioners[spec],
					},
				)
				frappe.db.set_value("Healthcare Appointment", appt.name, "encounter", enc.name)

	def _seed_branch_public_website(self) -> None:
		slug = frappe.scrub(self.branch).replace("_", "-")[:50]
		dept_icons = {
			"CARD": "cardiology",
			"PED": "pediatrics",
			"ORT": "orthopedics",
			"DER": "dermatology",
			"DEN": "dentistry",
			"RAD": "radiology",
			"LAB": "lab",
			"PHM": "pharmacy",
			"ER": "emergency",
		}
		depts = self.ctx.get("departments") or {}
		for code, dept_name in depts.items():
			icon = dept_icons.get(code, "general")
			frappe.db.set_value(
				"Healthcare Department",
				dept_name,
				{
					"publish_on_website": 1 if code in dept_icons else 0,
					"website_icon": icon,
					"website_display_order": list(depts.keys()).index(code) * 10 if code in depts else 0,
					"website_description_ar": f"قسم {code} — رعاية متخصصة",
					"website_description_en": f"{code} department — specialized care",
				},
				update_modified=False,
			)

		for spec, pr_name in (self.ctx.get("practitioners") or {}).items():
			frappe.db.set_value(
				"Healthcare Practitioner",
				pr_name,
				{
					"publish_on_website": 1,
					"years_of_experience": 8 + (len(spec) % 7),
					"website_rating": 4.7 + (len(spec) % 3) * 0.1,
					"website_bio_ar": "طبيب متخصص ذو خبرة واسعة في الرعاية السريرية.",
					"website_bio_en": "Experienced specialist focused on high-quality patient care.",
				},
				update_modified=False,
			)

		site_url = f"/hospital?site={quote(slug)}"
		if frappe.db.exists("Healthcare Branch Website", self.branch):
			frappe.db.set_value(
				"Healthcare Branch Website",
				self.branch,
				{
					"is_enabled": 1,
					"site_slug": slug,
					"hospital_name_ar": "مستشفى الحياة",
					"hospital_name_en": f"{DEMO_MARKER} Al-Hayat Hospital",
					"tagline_ar": "رعايتكم... أولويتنا",
					"tagline_en": "Your care... our priority",
					"hero_text_ar": "مستشفى متكامل يقدم رعاية صحية شاملة بأحدث التقنيات الطبية.",
					"hero_text_en": "A full-service hospital delivering comprehensive care with modern medical technology.",
					"hero_image": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80",
					"contact_phone": "+20 100 000 0000",
					"contact_email": "info@example.com",
					"stat_years": 15,
					"enable_online_shop": 1,
				},
				update_modified=False,
			)
		else:
			self._insert(
				"Healthcare Branch Website",
				{
					"branch": self.branch,
					"company": self.company,
					"is_enabled": 1,
					"site_slug": slug,
					"hospital_name_ar": "مستشفى الحياة",
					"hospital_name_en": f"{DEMO_MARKER} Al-Hayat Hospital",
					"tagline_ar": "رعايتكم... أولويتنا",
					"tagline_en": "Your care... our priority",
					"hero_text_ar": "مستشفى متكامل يقدم رعاية صحية شاملة بأحدث التقنيات الطبية.",
					"hero_text_en": "A full-service hospital delivering comprehensive care with modern medical technology.",
					"hero_image": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80",
					"contact_phone": "+20 100 000 0000",
					"contact_email": "info@example.com",
					"stat_years": 15,
					"enable_online_shop": 1,
				},
			)
		self.ctx["hospital_site_url"] = site_url
		self.ctx["web_booking_url"] = site_url
		self._bump("Healthcare Branch Website")

	def _seed_inventory_and_finance(self) -> None:
		wh_name = f"{DEMO_MARKER} Pharmacy WH"
		wh = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": self.company}, "name")
		if not wh:
			wh_doc = self._insert(
				"Warehouse",
				{
					"warehouse_name": wh_name,
					"warehouse_code": f"HC{self.branch[-4:].upper()}"[:10],
					"company": self.company,
				},
			)
			wh = wh_doc.name
		self.ctx["warehouse"] = wh

		items: list[str] = []
		for code, label, rate in PHARMACY_ITEMS:
			item_code = f"{DEMO_MARKER}{code}"
			existing = _resolve_item_name(item_code, self.company)
			if existing:
				items.append(existing)
				continue
			item_payload: dict = {
				"item_code": item_code,
				"item_name": f"{DEMO_MARKER} {label}",
				"company": self.company,
				"stock_uom": "Nos",
				"is_stock_item": 1,
			}
			if _item_has_field("standard_rate"):
				item_payload["standard_rate"] = rate
			if _item_has_field("product_type"):
				item_payload["product_type"] = "Consumable"
			item = self._insert("Item", item_payload)
			items.append(item.name)

		if items and not frappe.db.exists("Stock Entry", {"remarks": f"{DEMO_MARKER} opening stock"}):
			se_meta = frappe.get_meta("Stock Entry")
			se_payload: dict = {
				"doctype": "Stock Entry",
				"company": self.company,
				"posting_date": today(),
				"remarks": f"{DEMO_MARKER} opening stock",
				"items": [
					_stock_entry_item_row(
						item_name,
						wh,
						200,
						_demo_pharmacy_item_rate(
							frappe.db.get_value("Item", item_name, "item_code") or ""
						),
					)
					for item_name in items[:5]
				],
			}
			if se_meta.has_field("branch"):
				se_payload["branch"] = self.branch
			if se_meta.has_field("purpose"):
				se_payload["purpose"] = "Material Receipt"
			elif se_meta.has_field("stock_entry_type"):
				se_payload["stock_entry_type"] = "Material Receipt"
			if se_meta.has_field("to_warehouse"):
				se_payload["to_warehouse"] = wh
			se = frappe.get_doc(se_payload)
			se.insert(ignore_permissions=True)
			try:
				se.submit()
				self._bump("Stock Entry")
			except Exception:
				frappe.log_error(frappe.get_traceback(), "DEMO-HC stock entry submit")

		for ic in items[:3]:
			if not frappe.db.exists(
				"Healthcare Item Par Level",
				{"company": self.company, "branch": self.branch, "item": ic},
			):
				self._insert(
					"Healthcare Item Par Level",
					{
						"company": self.company,
						"branch": self.branch,
						"item": ic,
						"warehouse": wh,
						"par_level": 50,
						"reorder_qty": 100,
					},
				)

		ipd_unit = self.ctx.get("units", {}).get("IPD")
		if ipd_unit and items:
			self._insert(
				"Healthcare Ward Requisition",
				{
					"requisition_date": today(),
					"ward_service_unit": ipd_unit,
					"company": self.company,
					"branch": self.branch,
					"status": "Submitted",
					"items": [{"item": items[0], "qty": 10, "uom": "Nos"}],
				},
			)

		for idx, patient in enumerate(self.ctx.get("patients") or []):
			if idx % 2 != 0:
				continue
			customer = frappe.db.get_value("Healthcare Patient", patient, "billing_customer")
			if not customer:
				continue
			billing_item = self._demo_billing_item()
			charge = self._insert(
				"Healthcare Service Charge",
				{
					"naming_series": "HSC-.#####",
					"patient": patient,
					"billing_customer": customer,
					"company": self.company,
					"branch": self.branch,
					"posting_date": add_days(today(), -(idx % 10)),
					"status": "Draft",
					"reporting_tag": REPORTING_TAG,
					"items": [
						_service_charge_line(billing_item, "Consultation fee", 1, 350),
						_service_charge_line(billing_item, "Laboratory panel", 1, 450),
					],
				},
			)
			if idx % 4 == 0 and self.include_financial:
				self._maybe_create_sales_invoice(customer, patient, charge.name, idx)

	def _maybe_create_sales_invoice(self, customer: str, patient: str, charge_name: str, idx: int) -> None:
		if not frappe.db.exists("DocType", "Sales Invoice"):
			return
		try:
			billing_item = self._demo_billing_item()
			si = frappe.get_doc(
				{
					"doctype": "Sales Invoice",
					"customer": customer,
					"company": self.company,
					"branch": self.branch if frappe.get_meta("Sales Invoice").has_field("branch") else None,
					"posting_date": add_days(today(), -(idx % 10)),
					"due_date": add_days(today(), 15),
					"remarks": f"{DEMO_MARKER} OPD billing {patient}",
					"items": [_invoice_item_row(billing_item, 1, 350)],
				}
			)
			si.insert(ignore_permissions=True)
			si.submit()
			self._bump("Sales Invoice")
			frappe.db.set_value("Healthcare Service Charge", charge_name, "status", "Invoiced")
			frappe.db.set_value("Healthcare Service Charge", charge_name, "sales_invoice", si.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"DEMO-HC sales invoice skipped for {patient}")
