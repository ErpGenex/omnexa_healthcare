# -*- coding: utf-8 -*-
import frappe
from frappe import _


def get_context(context):
    context.title = _("Telemedicine Doctor Portal")
    context.description = _("Doctor telemedicine dashboard")
    return context
