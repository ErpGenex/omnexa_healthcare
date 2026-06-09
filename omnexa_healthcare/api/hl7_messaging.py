# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""HL7 v2 ADT / ORM / ORU messaging adapters."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def hl7_send_adt(patient: str, event: str = "A08") -> dict:
	"""Build ADT^A01/A08 message for patient registration/update."""
	doc = frappe.get_doc("Healthcare Patient", patient)
	msg = _build_adt(doc, event)
	return {"message": msg, "event": event}


@frappe.whitelist()
def hl7_send_orm(service_request: str) -> dict:
	sr = frappe.get_doc("Healthcare Service Request", service_request)
	msg = (
		f"MSH|^~\\&|OMNEXA|{sr.company}|LAB|EXT|{now_datetime()}||ORM^O01|{sr.name}|P|2.5\r"
		f"PID|1||{sr.patient}^^^MRN||{sr.patient_display or sr.patient}\r"
		f"ORC|NW|{sr.name}|||||||{sr.authored_on}\r"
		f"OBR|1|{sr.name}||{sr.request_loinc or sr.request_title}^^LOINC\r"
	)
	return {"message": msg, "service_request": sr.name}


@frappe.whitelist()
def hl7_receive_oru(message: str) -> dict:
	from omnexa_healthcare.api.lab_lis import api_hl7_oru_inbound

	return api_hl7_oru_inbound(message)


def _build_adt(patient, event: str) -> str:
	return (
		f"MSH|^~\\&|OMNEXA|{patient.company}|HIS|EXT|{now_datetime()}||ADT^{event}|{patient.name}|P|2.5\r"
		f"PID|1||{patient.name}^^^MRN||{patient.full_name}||{patient.birth_date or ''}|{patient.gender or ''}\r"
		f"PV1|1|O|{patient.branch}|||||||||||||||||||||||||||||||||||||||\r"
	)
