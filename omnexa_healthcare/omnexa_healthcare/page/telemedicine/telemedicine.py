# -*- coding: utf-8 -*-
import frappe
from frappe import _


def get_context(context):
    context.title = _("Telemedicine Patient Portal")
    context.description = _("Remote healthcare consultations")
    return context
