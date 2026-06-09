# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Full Healthcare workspace — auto-discovery + ERP bridge + all reports."""

from __future__ import annotations

import json
import re

import frappe

WorkspaceLink = tuple[str, str, str]  # link_type, link_to, label

# Curated sections (priority order) — anything missing is auto-added at the end.
WORKSPACE_SECTIONS: list[tuple[str, list[WorkspaceLink]]] = [
	(
		"📊 Dashboards & Portals",
		[
			("Page", "healthcare-executive-dashboard", "Executive Dashboard"),
			("Page", "healthcare-appointment-calendar", "Appointment Calendar"),
			("Page", "healthcare-patient-queue", "Patient Queue"),
			("Page", "healthcare-practitioner-roster", "Practitioner Roster"),
			("Page", "healthcare-in-basket", "In Basket"),
			("Page", "healthcare-er-board", "ER Board"),
			("Page", "healthcare-lab-workbench", "Lab Workbench"),
			("Page", "healthcare-radiology-worklist", "Radiology Worklist"),
			("Page", "healthcare-dicom-viewer", "DICOM Viewer"),
			("Page", "healthcare-pharmacy-desk", "Pharmacy Desk"),
			("Page", "healthcare-patient-portal", "Patient Portal"),
			("Page", "healthcare-patient-mobile", "Patient Mobile"),
			("Page", "healthcare-physician-mobile", "Physician Mobile"),
		],
	),
	(
		"🏢 Organization & Setup",
		[
			("DocType", "Company", "Company"),
			("DocType", "Branch", "Branch"),
			("DocType", "Healthcare Settings", "Healthcare Settings"),
			("DocType", "Healthcare Facility Profile", "Facility Profile"),
			("DocType", "Healthcare Department", "Department"),
			("DocType", "Healthcare Service Unit", "Service Unit"),
			("DocType", "Healthcare Specialty", "Specialty"),
			("DocType", "Healthcare Service Catalog", "Service Catalog"),
			("DocType", "Healthcare Consultation Fee Rule", "Consultation Fees"),
			("DocType", "Healthcare Icd10 Code", "ICD-10 Codes"),
			("DocType", "Healthcare Snomed Code", "SNOMED Codes"),
			("DocType", "Healthcare Drg Code", "DRG Codes"),
			("DocType", "Healthcare Clinical Template", "Clinical Templates"),
			("DocType", "Healthcare Procedure", "Procedures"),
			("DocType", "Healthcare Lab Test Panel", "Lab Test Panels"),
			("DocType", "Healthcare Lab Reference Range", "Lab Reference Ranges"),
			("DocType", "Healthcare Imaging Modality", "Imaging Modalities"),
			("DocType", "Healthcare Radiology Report Template", "Radiology Templates"),
			("DocType", "Healthcare Drug Interaction Rule", "Drug Interactions"),
		],
	),
	(
		"👤 MPI & Patient Access",
		[
			("DocType", "Healthcare Patient", "Patient"),
			("DocType", "Customer", "Customer (ERP)"),
			("DocType", "Healthcare Patient Merge Log", "Patient Merge Log"),
			("DocType", "Healthcare Patient Consent", "Patient Consent"),
			("DocType", "Healthcare Phi Access Log", "PHI Audit Log"),
			("DocType", "Healthcare Patient Push Notification", "Push Notifications"),
			("DocType", "Healthcare Mobile Device Token", "Mobile Devices"),
		],
	),
	(
		"🩺 Practitioners & OPD",
		[
			("DocType", "Healthcare Practitioner", "Practitioner"),
			("DocType", "Healthcare Appointment", "Appointment"),
			("DocType", "Healthcare Encounter", "Encounter"),
			("DocType", "Healthcare Episode Of Care", "Episode of Care"),
			("DocType", "Healthcare Procedure Order", "Procedure Order"),
			("DocType", "Healthcare In Basket Item", "In Basket Items"),
		],
	),
	(
		"📋 Clinical EMR",
		[
			("DocType", "Healthcare Clinical Condition", "Conditions"),
			("DocType", "Healthcare Allergy Intolerance", "Allergies"),
			("DocType", "Healthcare Immunization", "Immunizations"),
			("DocType", "Healthcare Medication Statement", "Medications"),
			("DocType", "Healthcare Observation", "Observations / Vitals"),
			("DocType", "Healthcare Service Request", "Orders & Requests"),
			("DocType", "Healthcare Diagnostic Report", "Diagnostic Reports"),
			("DocType", "Healthcare Clinical Cds Rule", "CDS Rules"),
			("DocType", "Healthcare Clinical Ai Insight", "AI Insights"),
			("DocType", "Healthcare Ambient Session", "Ambient AI"),
			("DocType", "Healthcare Voice Dictation", "Voice Dictation"),
		],
	),
	(
		"🚑 Emergency (ER)",
		[("DocType", "Healthcare Er Visit", "ER Visit")],
	),
	(
		"🏥 Inpatient · ADT · Nursing",
		[
			("DocType", "Healthcare Bed", "Bed"),
			("DocType", "Healthcare Admission", "Admission"),
			("DocType", "Healthcare Adt Transfer", "ADT Transfer"),
			("DocType", "Healthcare Nursing Care Plan", "Nursing Care Plan"),
			("DocType", "Healthcare Discharge Summary", "Discharge Summary"),
			("DocType", "Healthcare Nursing Observation Chart", "Nursing Chart"),
			("DocType", "Healthcare Medication Administration Record", "MAR"),
			("DocType", "Healthcare Barcode Scan Log", "Barcode Scan Log"),
		],
	),
	(
		"🔪 Surgery · OT · Anesthesia",
		[
			("DocType", "Healthcare Operating Room", "Operating Room"),
			("DocType", "Healthcare Surgical Case", "Surgical Case"),
			("DocType", "Healthcare Pre Op Checklist", "Pre-Op Checklist"),
			("DocType", "Healthcare Implant Trace", "Implant Trace"),
			("DocType", "Healthcare Anesthesia Record", "Anesthesia Record"),
			("DocType", "Healthcare Ot Consumable Issue", "OT Consumables"),
		],
	),
	(
		"🧪 Laboratory (LIS)",
		[
			("DocType", "Healthcare Lab Sample", "Lab Sample"),
			("DocType", "Healthcare Lab Qc Log", "QC Log"),
			("DocType", "Healthcare Lis Instrument Message", "LIS Instruments"),
		],
	),
	(
		"💊 Pharmacy",
		[("DocType", "Healthcare Medication Dispense", "Medication Dispense")],
	),
	(
		"🛡️ Insurance & RCM",
		[
			("DocType", "Healthcare Payer", "Payer"),
			("DocType", "Healthcare Insurance Plan", "Insurance Plan"),
			("DocType", "Healthcare Patient Coverage", "Patient Coverage"),
			("DocType", "Healthcare Prior Authorization", "Prior Authorization"),
			("DocType", "Healthcare Insurance Claim", "Insurance Claim"),
			("DocType", "Healthcare Claim Remittance", "Claim Remittance"),
			("DocType", "Healthcare Eligibility Check", "Eligibility Check"),
			("DocType", "Healthcare Nphies Claim Bundle", "NPHIES Bundle"),
			("DocType", "Healthcare X12 Transaction", "X12 EDI"),
		],
	),
	(
		"💰 Billing · Finance · ERP",
		[
			("DocType", "Healthcare Service Charge", "Service Charge"),
			("DocType", "Sales Invoice", "Sales Invoice"),
			("DocType", "Payment Entry", "Payment Entry"),
			("DocType", "Journal Entry", "Journal Entry"),
			("DocType", "Purchase Invoice", "Purchase Invoice"),
			("DocType", "Supplier", "Supplier"),
		],
	),
	(
		"📦 Inventory & Supply",
		[
			("DocType", "Healthcare Ward Requisition", "Ward Requisition"),
			("DocType", "Healthcare Item Par Level", "Par Levels"),
			("DocType", "Item", "Item"),
			("DocType", "Item Group", "Item Group"),
			("DocType", "Warehouse", "Warehouse"),
			("DocType", "Stock Entry", "Stock Entry"),
			("DocType", "Stock Reconciliation", "Stock Reconciliation"),
			("DocType", "Material Request", "Material Request"),
			("DocType", "Purchase Order", "Purchase Order"),
			("DocType", "UOM", "UOM"),
			("DocType", "Batch", "Batch"),
			("DocType", "Serial No", "Serial No"),
		],
	),
	(
		"👥 HR & Users",
		[
			("DocType", "Employee", "Employee"),
			("DocType", "User", "User"),
			("DocType", "Role", "Role"),
		],
	),
	(
		"🌍 Population Health",
		[
			("DocType", "Healthcare Patient Cohort", "Patient Cohorts"),
			("DocType", "Healthcare Care Gap", "Care Gaps"),
			("DocType", "Healthcare Secure Message", "Secure Messages"),
		],
	),
]

REPORT_SECTIONS: list[tuple[str, list[WorkspaceLink]]] = [
	("📈 Reports · Scheduling & OPD", []),
	("📈 Reports · Clinical", []),
	("📈 Reports · Inpatient", []),
	("📈 Reports · Laboratory", []),
	("📈 Reports · Radiology", []),
	("📈 Reports · Pharmacy", []),
	("📈 Reports · Surgery", []),
	("📈 Reports · RCM & Finance", []),
]

# Map report name keywords → section index
_REPORT_BUCKETS: list[tuple[str, tuple[str, ...]]] = [
	("📈 Reports · Scheduling & OPD", ("appointment", "practitioner", "roster", "telehealth", "no show", "lead time", "unpaid booking")),
	("📈 Reports · Clinical", ("encounter", "diagnosis", "allergy", "immunization", "episode", "template")),
	("📈 Reports · Inpatient", ("inpatient", "admission", "los", "icu", "mar", "nursing", "ward")),
	("📈 Reports · Laboratory", ("lab", "abnormal", "diagnostic category", "pending lab")),
	("📈 Reports · Radiology", ("radiology", "imaging", "structured report")),
	("📈 Reports · Pharmacy", ("dispense", "drug", "pharmacy", "par")),
	("📈 Reports · Surgery", ("or ", "ot ", "consumable")),
	("📈 Reports · RCM & Finance", ("insurance", "claim", "payer", "copay", "cash", "charge", "revenue", "procedure", "prior auth")),
]

_SHORTCUT_COLORS = ("Blue", "Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		if not frappe.db.exists("DocType", link_to):
			return False
		meta = frappe.get_meta(link_to, cached=True)
		return bool(meta and not meta.istable)
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Dashboard":
		return bool(frappe.db.exists("Dashboard", link_to))
	return False


def _human_label(name: str) -> str:
	return name.replace("Healthcare ", "").strip()


def _report_ref_doctype(report_name: str) -> str | None:
	return frappe.db.get_value("Report", report_name, "ref_doctype")


def _discover_healthcare_doctypes(seen: set[tuple[str, str]]) -> list[WorkspaceLink]:
	out: list[WorkspaceLink] = []
	for name in frappe.get_all(
		"DocType",
		filters={"module": "Omnexa Healthcare", "istable": 0},
		pluck="name",
		order_by="name",
	):
		key = ("DocType", name)
		if key in seen:
			continue
		if _link_exists("DocType", name):
			out.append(("DocType", name, _human_label(name)))
	return out


def _discover_healthcare_pages(seen: set[tuple[str, str]]) -> list[WorkspaceLink]:
	out: list[WorkspaceLink] = []
	for name in frappe.get_all("Page", filters={"module": "Omnexa Healthcare"}, pluck="name", order_by="name"):
		key = ("Page", name)
		if key in seen:
			continue
		label = name.replace("healthcare-", "").replace("-", " ").title()
		out.append(("Page", name, label))
	return out


def _discover_healthcare_reports(seen: set[tuple[str, str]]) -> list[WorkspaceLink]:
	out: list[WorkspaceLink] = []
	for name in frappe.get_all("Report", filters={"module": "Omnexa Healthcare"}, pluck="name", order_by="name"):
		key = ("Report", name)
		if key in seen:
			continue
		out.append(("Report", name, _human_label(name)))
	return out


def _bucket_report(report_name: str) -> str:
	low = report_name.lower()
	for section, keywords in _REPORT_BUCKETS:
		if any(k in low for k in keywords):
			return section
	return "📈 Reports · Other"


def _build_report_sections(seen: set[tuple[str, str]]) -> list[tuple[str, list[WorkspaceLink]]]:
	buckets: dict[str, list[WorkspaceLink]] = {s: list(items) for s, items in REPORT_SECTIONS}
	buckets["📈 Reports · Other"] = []
	for name in frappe.get_all("Report", filters={"module": "Omnexa Healthcare"}, pluck="name", order_by="name"):
		key = ("Report", name)
		if key in seen:
			continue
		section = _bucket_report(name)
		buckets.setdefault(section, []).append(("Report", name, _human_label(name)))
	return [(s, items) for s, items in buckets.items() if items]


def _row_from_link(link_type: str, link_to: str, label: str) -> dict:
	row = {"label": label, "type": "Link", "link_type": link_type, "link_to": link_to}
	if link_type == "Report":
		row["is_query_report"] = 1
		ref = _report_ref_doctype(link_to)
		if ref:
			row["report_ref_doctype"] = ref
	return row


def _build_link_rows() -> list[dict]:
	rows: list[dict] = []
	seen: set[tuple[str, str]] = set()

	def add_section(section_label: str, items: list[WorkspaceLink]) -> None:
		valid = [(t, to, label) for t, to, label in items if _link_exists(t, to)]
		if not valid:
			return
		rows.append({"label": section_label, "type": "Card Break", "link_type": "DocType"})
		for link_type, link_to, label in valid:
			key = (link_type, link_to)
			if key in seen:
				continue
			seen.add(key)
			rows.append(_row_from_link(link_type, link_to, label))

	for section_label, items in WORKSPACE_SECTIONS:
		add_section(section_label, items)

	# Auto: any healthcare pages not yet listed
	extra_pages = _discover_healthcare_pages(seen)
	if extra_pages:
		add_section("📱 Pages (auto)", extra_pages)

	# Auto: any healthcare doctypes not yet listed
	extra_dt = _discover_healthcare_doctypes(seen)
	if extra_dt:
		add_section("📁 Healthcare DocTypes (auto)", extra_dt)

	# Reports — bucketed + full coverage
	for section_label, items in _build_report_sections(seen):
		add_section(section_label, items)

	return rows


def _build_shortcuts(link_rows: list[dict]) -> list[dict]:
	"""Workspace home shortcuts — one per link (pages & doctypes first)."""
	shortcuts: list[dict] = []
	idx = 0
	priority_types = ("Page", "DocType", "Report", "Dashboard")
	links = [r for r in link_rows if r.get("type") == "Link"]
	for lt in priority_types:
		for row in links:
			if row.get("link_type") != lt:
				continue
			entry = {
				"label": row["label"],
				"link_to": row["link_to"],
				"type": row["link_type"],
				"color": _SHORTCUT_COLORS[idx % len(_SHORTCUT_COLORS)],
			}
			if lt == "DocType":
				entry["doc_view"] = "List"
			if lt == "Report" and row.get("report_ref_doctype"):
				entry["report_ref_doctype"] = row["report_ref_doctype"]
			shortcuts.append(entry)
			idx += 1
	return shortcuts


def _onboarding_blocks(existing_content: str | None) -> list[dict]:
	if not existing_content:
		return []
	try:
		blocks = json.loads(existing_content)
	except json.JSONDecodeError:
		return []
	return [b for b in blocks if b.get("type") == "onboarding"]


def _build_content(link_rows: list[dict], ws) -> str:
	"""Rebuild workspace home layout — content blocks must reference shortcut labels."""
	content: list[dict] = []
	content.extend(_onboarding_blocks(ws.content))
	content.append(
		{
			"id": "healthcare-title",
			"type": "header",
			"data": {"text": '<span class="h4"><b>Healthcare</b></span>', "col": 12},
		}
	)

	section_idx = 0
	link_idx = 0
	for row in link_rows:
		if row.get("type") == "Card Break":
			if section_idx:
				content.append({"id": f"healthcare-sp-{section_idx}", "type": "spacer", "data": {"col": 12}})
			content.append(
				{
					"id": f"healthcare-sec-{section_idx}",
					"type": "header",
					"data": {"text": f'<span class="h5"><b>{row["label"]}</b></span>', "col": 12},
				}
			)
			section_idx += 1
			continue
		content.append(
			{
				"id": f"healthcare-lnk-{link_idx}",
				"type": "shortcut",
				"data": {"shortcut_name": row["label"], "col": 4},
			}
		)
		link_idx += 1

	if ws.number_cards:
		content.append({"id": "healthcare-kpi-sp", "type": "spacer", "data": {"col": 12}})
		content.append(
			{
				"id": "healthcare-kpi-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📊 KPIs</b></span>', "col": 12},
			}
		)
		for idx, nc in enumerate(ws.number_cards):
			content.append(
				{
					"id": f"healthcare-nc-{idx}",
					"type": "number_card",
					"data": {"number_card_name": nc.number_card_name, "col": 4},
				}
			)

	if ws.charts:
		content.append({"id": "healthcare-ch-sp", "type": "spacer", "data": {"col": 12}})
		content.append(
			{
				"id": "healthcare-ch-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📈 Charts</b></span>', "col": 12},
			}
		)
		for idx, ch in enumerate(ws.charts):
			content.append(
				{
					"id": f"healthcare-ch-{idx}",
					"type": "chart",
					"data": {"chart_name": ch.label or ch.chart_name, "col": 4},
				}
			)

	return json.dumps(content, separators=(",", ":"))


def sync_healthcare_workspace_menu(*, save: bool = True, rebuild: bool = True) -> dict:
	"""Rebuild Healthcare workspace sidebar + home shortcuts (full catalog)."""
	stats = {"sections": 0, "links": 0, "shortcuts": 0}
	if not frappe.db.exists("Workspace", "Healthcare"):
		return stats

	new_rows = _build_link_rows()
	link_rows = [r for r in new_rows if r.get("type") == "Link"]
	new_shortcuts = _build_shortcuts(new_rows)

	ws = frappe.get_doc("Workspace", "Healthcare")
	if rebuild:
		ws.set("links", [])
		ws.set("shortcuts", [])

	for row in new_rows:
		if row["type"] == "Card Break":
			stats["sections"] += 1
		else:
			stats["links"] += 1
		ws.append("links", row)

	for sc in new_shortcuts:
		ws.append("shortcuts", sc)
	stats["shortcuts"] = len(new_shortcuts)

	ws.content = _build_content(new_rows, ws)
	stats["content_blocks"] = len(json.loads(ws.content))

	if save:
		ws.flags.ignore_permissions = True
		ws.save()
		frappe.clear_cache(doctype="Workspace")

	stats["total_links"] = len(link_rows)
	return stats


@frappe.whitelist()
def get_workspace_coverage() -> dict:
	rows = _build_link_rows()
	link_rows = [r for r in rows if r.get("type") == "Link"]
	dts = frappe.get_all("DocType", filters={"module": "Omnexa Healthcare", "istable": 0}, pluck="name")
	catalogued_dt = {r["link_to"] for r in link_rows if r.get("link_type") == "DocType"}
	reports = frappe.get_all("Report", filters={"module": "Omnexa Healthcare"}, pluck="name")
	catalogued_reports = {r["link_to"] for r in link_rows if r.get("link_type") == "Report"}
	return {
		"sections": len([r for r in rows if r.get("type") == "Card Break"]),
		"links_catalogued": len(link_rows),
		"pages": len([r for r in link_rows if r.get("link_type") == "Page"]),
		"doctypes": len([r for r in link_rows if r.get("link_type") == "DocType"]),
		"reports": len([r for r in link_rows if r.get("link_type") == "Report"]),
		"healthcare_doctypes_total": len(dts),
		"healthcare_doctypes_missing": sorted(set(dts) - catalogued_dt),
		"healthcare_reports_total": len(reports),
		"healthcare_reports_missing": sorted(set(reports) - catalogued_reports),
		"shortcuts_planned": len(_build_shortcuts(rows)),
	}
