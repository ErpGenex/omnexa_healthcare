# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Seed world-class gap-closure demo operations (blood bank, CSSD, compensation, QMS)."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, add_months, flt, today


def seed_world_class_gap_operations(seeder) -> None:
	"""Populate Blood Bank, CSSD, physician compensation, CAPA, infection surveillance demo."""
	if not _has_doctype("Healthcare Blood Donor"):
		return

	company = seeder.company
	branch = seeder.branch
	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER

	patients = seeder.ctx.get("patients") or []
	practitioners = seeder.ctx.get("practitioners") or {}
	branch_tag = frappe.scrub(branch).upper()[:12]

	# Blood bank
	donors: list[str] = []
	for idx, (name, group) in enumerate(
		[
			("Ahmed Donor", "O+"),
			("Sara Donor", "A+"),
			("Khaled Donor", "B+"),
			("Mona Donor", "AB+"),
		]
	):
		donor_name = f"{DEMO_MARKER} {branch_tag} {name}"
		donor = frappe.db.get_value("Healthcare Blood Donor", {"donor_name": donor_name, "branch": branch}, "name")
		if not donor:
			donor = seeder._insert(
				"Healthcare Blood Donor",
				{
					"donor_name": donor_name,
					"blood_group": group,
					"last_donation_date": add_days(today(), -30 - idx * 7),
					"status": "Active",
					"company": company,
					"branch": branch,
				},
			).name
		donors.append(donor)

	blood_units: list[str] = []
	for idx, donor in enumerate(donors):
		group = frappe.db.get_value("Healthcare Blood Donor", donor, "blood_group")
		unit_number = f"{DEMO_MARKER}{branch_tag}-BU-{idx + 1:03d}"
		unit_name = frappe.db.get_value("Healthcare Blood Unit", {"unit_number": unit_number}, "name")
		if unit_name:
			blood_units.append(unit_name)
			continue
		unit = seeder._insert(
			"Healthcare Blood Unit",
			{
				"unit_number": unit_number,
				"blood_group": group,
				"component": "Packed RBC",
				"donor": donor,
				"collection_date": add_days(today(), -10 - idx),
				"expiry_date": add_days(today(), 25 - idx),
				"status": "Available" if idx < 3 else "Reserved",
				"company": company,
				"branch": branch,
			},
		)
		blood_units.append(unit.name)

	if patients and blood_units and not frappe.db.exists(
		"Healthcare Transfusion Order",
		{"patient": patients[0], "blood_unit": blood_units[0], "branch": branch},
	):
		seeder._insert(
			"Healthcare Transfusion Order",
			{
				"patient": patients[0],
				"blood_unit": blood_units[0],
				"cross_match_result": "Compatible",
				"ordered_by": practitioners.get("CAR") or practitioners.get("GEN"),
				"status": "Approved",
				"company": company,
				"branch": branch,
			},
		)

	# CSSD
	instruments: list[str] = []
	for code, label in (
		("OT-SET-01", "Major Laparotomy Set"),
		("OT-SET-02", "Orthopedic Tray"),
		("OT-TRAY-01", "Minor Procedure Tray"),
	):
		instrument_code = f"{DEMO_MARKER}{branch_tag}-{code}"
		inst_name = frappe.db.get_value("Healthcare Cssd Instrument", instrument_code, "name")
		if not inst_name:
			inst = seeder._insert(
				"Healthcare Cssd Instrument",
				{
					"instrument_code": instrument_code,
					"instrument_name": f"{DEMO_MARKER} {label}",
					"instrument_type": "Set",
					"status": "Sterile",
					"last_sterilization_date": add_days(today(), -2),
					"sterility_expiry_date": add_days(today(), 5),
					"company": company,
					"branch": branch,
				},
			)
			inst_name = inst.name
		instruments.append(inst_name)
		if not frappe.db.exists("Healthcare Sterilization Cycle", {"instrument": inst_name, "branch": branch}):
			seeder._insert(
				"Healthcare Sterilization Cycle",
				{
					"instrument": inst_name,
					"cycle_type": "Autoclave",
					"cycle_datetime": f"{add_days(today(), -2)} 08:00:00",
					"result": "Pass",
					"company": company,
					"branch": branch,
				},
			)

	# Physician compensation
	for spec_key, model, pct in (
		("CAR", "Revenue Share", 35),
		("ORT", "Per Procedure", 0),
		("GEN", "Per Visit", 0),
		("SUR", "Per Surgery", 0),
	):
		pr = practitioners.get(spec_key)
		if not pr:
			continue
		code = f"{DEMO_MARKER}{branch_tag}-COMP-{spec_key}"
		if frappe.db.exists("Healthcare Physician Compensation Rule", code):
			continue
		payload = {
			"rule_code": code,
			"practitioner": pr,
			"compensation_model": model,
			"effective_from": add_months(today(), -6),
			"is_active": 1,
			"company": company,
			"branch": branch,
		}
		if pct:
			payload["share_percent"] = pct
		else:
			payload["fixed_amount"] = 350 if model == "Per Visit" else 2500
		seeder._insert("Healthcare Physician Compensation Rule", payload)
		seeder._insert(
			"Healthcare Physician Settlement",
			{
				"practitioner": pr,
				"period_start": add_months(today(), -1),
				"period_end": add_days(today(), -1),
				"gross_revenue": flt(45000 + hash(spec_key) % 20000),
				"physician_share": flt(12000 + hash(spec_key) % 8000),
				"status": "Approved" if spec_key == "CAR" else "Draft",
				"company": company,
				"branch": branch,
			},
		)

	# Quality & infection control
	if not frappe.db.exists(
		"Healthcare Quality Corrective Action",
		{"title": f"{DEMO_MARKER} Reduce medication near-miss events", "branch": branch},
	):
		seeder._insert(
			"Healthcare Quality Corrective Action",
			{
				"title": f"{DEMO_MARKER} Reduce medication near-miss events",
				"source": "Near Miss",
				"severity": "Medium",
				"root_cause": "Barcode scanning skipped during night shift (demo).",
				"corrective_action": "Mandatory dual verification + eMAR barcode enforcement.",
				"status": "In Progress",
				"due_date": add_days(today(), 30),
				"company": company,
				"branch": branch,
			},
		)
	if patients and not frappe.db.exists(
		"Healthcare Infection Surveillance Case",
		{"patient": patients[5], "branch": branch, "infection_type": "HAI"},
	):
		seeder._insert(
			"Healthcare Infection Surveillance Case",
			{
				"patient": patients[5],
				"infection_type": "HAI",
				"onset_date": add_days(today(), -7),
				"isolation_required": 1,
				"status": "Under Surveillance",
				"company": company,
				"branch": branch,
			},
		)

	# Telehealth + home care + RPM samples (wave 2 DTs)
	if patients and _has_doctype("Healthcare Telehealth Session"):
		appt = frappe.db.get_value(
			"Healthcare Appointment",
			{"patient": patients[2], "company": company, "branch": branch},
			"name",
		)
		if appt and not frappe.db.exists("Healthcare Telehealth Session", {"appointment": appt}):
			seeder._insert(
				"Healthcare Telehealth Session",
				{
					"appointment": appt,
					"patient": patients[2],
					"practitioner": practitioners.get("GEN"),
					"room_id": f"{DEMO_MARKER}tele-001",
					"join_url": "https://meet.jit.si/erpgenex-demo-consult",
					"status": "Completed",
					"company": company,
					"branch": branch,
				},
			)

	if patients and _has_doctype("Healthcare Home Visit Request"):
		seeder._insert(
			"Healthcare Home Visit Request",
			{
				"patient": patients[8],
				"visit_type": "Nursing",
				"scheduled_datetime": f"{add_days(today(), 2)} 10:00:00",
				"address": "Demo home address — Nasr City, Cairo",
				"practitioner": practitioners.get("PTH"),
				"status": "Scheduled",
				"company": company,
				"branch": branch,
			},
		)

	if patients and _has_doctype("Healthcare Remote Monitoring Reading"):
		seeder._insert(
			"Healthcare Remote Monitoring Reading",
			{
				"patient": patients[4],
				"metric_type": "Blood Pressure",
				"value": 128,
				"unit": "mmHg",
				"reading_datetime": f"{today()} 07:30:00",
				"alert_level": "Normal",
				"company": company,
			},
		)

	seeder.ctx["world_class_gap_seeded"] = True
	seed_family_medicine_demo(seeder)


def seed_family_medicine_demo(seeder) -> None:
	if not _has_doctype("Healthcare Family Unit"):
		return

	from frappe.utils import add_days, add_months, today

	from omnexa_healthcare.utils.branch_demo_seed import DEMO_MARKER

	company = seeder.company
	branch = seeder.branch
	patients = seeder.ctx.get("patients") or []
	if len(patients) < 4:
		return

	branch_tag = frappe.scrub(branch).upper()[:12]
	family_number = f"{DEMO_MARKER}{branch_tag}-FAM-001"
	fm_practitioner = (seeder.ctx.get("practitioners") or {}).get("FM")

	head = patients[0]
	spouse = patients[1]
	child_a = patients[3]
	child_b = patients[7] if len(patients) > 7 else patients[2]

	fu_name = frappe.db.get_value("Healthcare Family Unit", {"family_number": family_number}, "name")
	if not fu_name:
		fu = seeder._insert(
			"Healthcare Family Unit",
			{
				"family_number": family_number,
				"family_name": f"{DEMO_MARKER} Hassan Household",
				"head_of_family": head,
				"primary_care_practitioner": fm_practitioner,
				"household_status": "Active",
				"shared_genetic_risk_notes": "Type 2 diabetes and hypertension in first-degree relatives — enhanced screening.",
				"company": company,
				"branch": branch,
				"members": [
					{"patient": head, "relationship": "Head", "is_primary_contact": 1, "enrollment_date": today()},
					{"patient": spouse, "relationship": "Spouse", "enrollment_date": today()},
					{"patient": child_a, "relationship": "Child", "enrollment_date": today()},
					{"patient": child_b, "relationship": "Child", "enrollment_date": today()},
				],
			},
		)
		fu_name = fu.name
	else:
		fu_name = fu_name

	history_specs = [
		("Diabetes", "Type 2 diabetes mellitus", "Father", "E11", "5A11"),
		("Hypertension", "Essential hypertension", "Mother", "I10", "BA00"),
		("Heart Disease", "Coronary artery disease", "Grandparent", "I25", ""),
	]
	for cat, desc, rel, icd10, icd11 in history_specs:
		if frappe.db.exists(
			"Healthcare Family History",
			{"family_unit": fu_name, "condition_description": desc, "relative_relationship": rel},
		):
			continue
		seeder._insert(
			"Healthcare Family History",
			{
				"family_unit": fu_name,
				"condition_category": cat,
				"condition_description": desc,
				"relative_relationship": rel,
				"icd10_code": icd10,
				"icd11_code": icd11 or None,
				"age_at_onset": 52 if cat != "Heart Disease" else 68,
				"company": company,
				"branch": branch,
			},
		)

	plan_title = f"{DEMO_MARKER} Annual preventive bundle"
	plan_name = frappe.db.get_value(
		"Healthcare Preventive Care Plan",
		{"family_unit": fu_name, "plan_title": plan_title},
		"name",
	)
	if not plan_name:
		seeder._insert(
			"Healthcare Preventive Care Plan",
			{
				"family_unit": fu_name,
				"patient": head,
				"plan_title": plan_title,
				"status": "Active",
				"start_date": today(),
				"end_date": add_months(today(), 12),
				"practitioner": fm_practitioner,
				"company": company,
				"branch": branch,
				"items": [
					{"screening_name": "HbA1c", "due_date": add_days(today(), 14), "status": "Due"},
					{"screening_name": "Lipid panel", "due_date": add_days(today(), 30), "status": "Scheduled"},
					{"screening_name": "Blood pressure check", "due_date": add_days(today(), -5), "status": "Overdue"},
					{"screening_name": "Influenza vaccine", "due_date": add_days(today(), 60), "status": "Due"},
				],
			},
		)

	if not frappe.db.exists("Healthcare Family Risk Score", {"family_unit": fu_name}):
		from omnexa_healthcare.api.family_risk_engine import compute_family_risk

		compute_family_risk(fu_name, head)

	seeder.ctx["family_medicine_demo_unit"] = fu_name


def _has_doctype(name: str) -> bool:
	return bool(frappe.db.exists("DocType", name))
