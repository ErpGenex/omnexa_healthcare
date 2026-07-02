# -*- coding: utf-8 -*-
import frappe
from frappe import _


def get_context(context):
    context.title = _("Telemedicine Admin Dashboard")
    context.description = _("Telemedicine administration and analytics")
    return context
