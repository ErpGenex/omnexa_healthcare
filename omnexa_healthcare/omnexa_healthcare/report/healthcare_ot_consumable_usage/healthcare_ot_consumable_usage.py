# Auto-generated Healthcare report pack
import frappe
from frappe import _
from omnexa_healthcare.report_pack._helpers import branch_conditions, date_conditions, require_company
from omnexa_healthcare.report_pack.executors import run_report


def execute(filters=None):
	return run_report("healthcare_ot_consumable_usage", filters)
