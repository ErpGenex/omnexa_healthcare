# Auto-generated Healthcare report pack
import frappe
from frappe import _
from omnexa_healthcare.report_pack.executors import run_report

# Audit hints: Currency columns emitted by report pack executor
_CURRENCY_COLUMNS = ("claim_amount", "total_amount")


def execute(filters=None):
	return run_report("healthcare_payer_aging", filters)
