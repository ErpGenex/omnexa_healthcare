app_name = "omnexa_healthcare"
app_title = "ErpGenEx — Healthcare"
app_publisher = "ErpGenEx"
app_description = "Healthcare vertical"
app_email = "dev@erpgenex.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["omnexa_core", "omnexa_accounting"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "omnexa_healthcare",
# 		"logo": "/assets/omnexa_healthcare/logo.png",
# 		"title": "Omnexa Healthcare",
# 		"route": "/omnexa_healthcare",
# 		"has_permission": "omnexa_healthcare.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/omnexa_healthcare/css/healthcare-rtl.css"
# app_include_js = "/assets/omnexa_healthcare/js/omnexa_healthcare.js"

# include js, css files in header of web template
# web_include_css = "/assets/omnexa_healthcare/css/omnexa_healthcare.css"
# web_include_js = "/assets/omnexa_healthcare/js/omnexa_healthcare.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omnexa_healthcare/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Healthcare Service Charge": "public/js/healthcare_service_charge.js",
	"Healthcare Medication Dispense": "public/js/healthcare_medication_dispense.js",
	"Healthcare Appointment": "public/js/healthcare_appointment.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "omnexa_healthcare/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "omnexa_healthcare.utils.jinja_methods",
# 	"filters": "omnexa_healthcare.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "omnexa_healthcare.install.enforce_supported_frappe_version"
before_migrate = "omnexa_healthcare.install.enforce_supported_frappe_version"
after_migrate = "omnexa_healthcare.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "omnexa_healthcare.uninstall.before_uninstall"
# after_uninstall = "omnexa_healthcare.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "omnexa_healthcare.utils.before_app_install"
# after_app_install = "omnexa_healthcare.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "omnexa_healthcare.utils.before_app_uninstall"
# after_app_uninstall = "omnexa_healthcare.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "omnexa_healthcare.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Healthcare Patient": "omnexa_healthcare.permissions.healthcare_patient_query_conditions",
	"Healthcare Appointment": "omnexa_healthcare.permissions.healthcare_appointment_query_conditions",
	"Healthcare Encounter": "omnexa_healthcare.permissions.healthcare_encounter_query_conditions",
	"Healthcare Episode Of Care": "omnexa_healthcare.permissions.healthcare_episode_of_care_query_conditions",
	"Healthcare Facility Profile": "omnexa_healthcare.permissions.healthcare_facility_profile_query_conditions",
	"Healthcare Department": "omnexa_healthcare.permissions.healthcare_department_query_conditions",
	"Healthcare Service Unit": "omnexa_healthcare.permissions.healthcare_service_unit_query_conditions",
	"Healthcare Clinical Condition": "omnexa_healthcare.permissions.healthcare_clinical_condition_query_conditions",
	"Healthcare Allergy Intolerance": "omnexa_healthcare.permissions.healthcare_allergy_intolerance_query_conditions",
	"Healthcare Medication Statement": "omnexa_healthcare.permissions.healthcare_medication_statement_query_conditions",
	"Healthcare Immunization": "omnexa_healthcare.permissions.healthcare_immunization_query_conditions",
	"Healthcare Observation": "omnexa_healthcare.permissions.healthcare_observation_query_conditions",
	"Healthcare Service Request": "omnexa_healthcare.permissions.healthcare_service_request_query_conditions",
	"Healthcare Diagnostic Report": "omnexa_healthcare.permissions.healthcare_diagnostic_report_query_conditions",
	"Healthcare Bed": "omnexa_healthcare.permissions.healthcare_bed_query_conditions",
	"Healthcare Admission": "omnexa_healthcare.permissions.healthcare_admission_query_conditions",
	"Healthcare Service Charge": "omnexa_healthcare.permissions.healthcare_service_charge_query_conditions",
	"Healthcare Medication Dispense": "omnexa_healthcare.permissions.healthcare_medication_dispense_query_conditions",
	"Healthcare Lab Sample": "omnexa_healthcare.permissions.healthcare_lab_sample_query_conditions",
	"Healthcare Practitioner": "omnexa_healthcare.permissions.healthcare_practitioner_query_conditions",
	"Healthcare Procedure Order": "omnexa_healthcare.permissions.healthcare_procedure_order_query_conditions",
	"Healthcare Patient Coverage": "omnexa_healthcare.permissions.healthcare_patient_coverage_query_conditions",
	"Healthcare Insurance Claim": "omnexa_healthcare.permissions.healthcare_insurance_claim_query_conditions",
	"Healthcare Operating Room": "omnexa_healthcare.permissions.healthcare_operating_room_query_conditions",
	"Healthcare Surgical Case": "omnexa_healthcare.permissions.healthcare_surgical_case_query_conditions",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {}

_BRANCH_VALIDATE = [
	"Healthcare Patient",
	"Healthcare Appointment",
	"Healthcare Facility Profile",
	"Healthcare Department",
	"Healthcare Service Unit",
	"Healthcare Encounter",
	"Healthcare Episode Of Care",
	"Healthcare Clinical Condition",
	"Healthcare Allergy Intolerance",
	"Healthcare Medication Statement",
	"Healthcare Immunization",
	"Healthcare Observation",
	"Healthcare Service Request",
	"Healthcare Diagnostic Report",
	"Healthcare Bed",
	"Healthcare Admission",
	"Healthcare Service Charge",
	"Healthcare Medication Dispense",
	"Healthcare Lab Sample",
	"Healthcare Procedure Order",
	"Healthcare Patient Coverage",
	"Healthcare Insurance Claim",
	"Healthcare Operating Room",
	"Healthcare Surgical Case",
	"Healthcare Ward Requisition",
	"Healthcare Ot Consumable Issue",
	"Healthcare Prior Authorization",
	"Healthcare Claim Remittance",
	"Healthcare Nursing Observation Chart",
	"Healthcare Medication Administration Record",
	"Healthcare Anesthesia Record",
	"Healthcare Patient Consent",
	"Healthcare Lab Qc Log",
	"Healthcare Er Visit",
	"Healthcare In Basket Item",
	"Healthcare Adt Transfer",
	"Healthcare Nursing Care Plan",
	"Healthcare Discharge Summary",
	"Healthcare Eligibility Check",
	"Healthcare Nphies Claim Bundle",
	"Healthcare Patient Cohort",
	"Healthcare Care Gap",
	"Healthcare Secure Message",
	"Healthcare Ambient Session",
	"Healthcare Voice Dictation",
	"Healthcare X12 Transaction",
]

for _dt in _BRANCH_VALIDATE:
	doc_events[_dt] = {
		"before_validate": "omnexa_healthcare.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_healthcare.permissions.enforce_branch_access_for_doc",
	}

doc_events["Healthcare Practitioner"] = {
	"before_validate": "omnexa_healthcare.permissions.populate_company_branch_from_user_context",
}

doc_events["Healthcare Patient"]["validate"] = [
	"omnexa_healthcare.permissions.enforce_branch_access_for_doc",
	"omnexa_healthcare.api.mpi.enforce_cross_branch_patient_policy",
]
doc_events["Healthcare Patient"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Patient"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Encounter"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Encounter"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Diagnostic Report"] = {
	"on_submit": "omnexa_healthcare.api.in_basket.notify_abnormal_diagnostic_report",
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": ["omnexa_healthcare.api.reminders.send_appointment_reminders"],
}
# 	"weekly": [
# 		"omnexa_healthcare.tasks.weekly"
# 	],
# 	"monthly": [
# 		"omnexa_healthcare.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "omnexa_healthcare.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "omnexa_healthcare.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "omnexa_healthcare.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["omnexa_healthcare.license_gate.before_request"]
# after_request = ["omnexa_healthcare.utils.after_request"]

# Job Events
# ----------
# before_job = ["omnexa_healthcare.utils.before_job"]
# after_job = ["omnexa_healthcare.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"omnexa_healthcare.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

