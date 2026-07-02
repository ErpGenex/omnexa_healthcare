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
app_include_css = [
	"/assets/omnexa_healthcare/css/healthcare-rtl.css",
	"/assets/omnexa_healthcare/css/healthcare-accessibility.css",
	"/assets/omnexa_healthcare/css/omnexa-journey.css",
]
app_include_js = [
	"/assets/omnexa_healthcare/js/healthcare_terminology.js",
	"/assets/omnexa_healthcare/js/omnexa-journey.js",
	"/assets/omnexa_healthcare/js/omnexa-journey-kit.js",
	"/assets/omnexa_healthcare/js/healthcare-navbar-lang.js",
	"/assets/omnexa_healthcare/js/healthcare-portal-factory.js",
	"/assets/omnexa_healthcare/js/dental-interactive-chart.js",
	"/assets/omnexa_healthcare/js/healthcare-department-desk.js",
]

# include js, css files in header of web template
web_include_css = [
	"/assets/omnexa_healthcare/css/hospital_website.css",
	"/assets/omnexa_healthcare/css/omnexa-journey.css",
	"/assets/omnexa_healthcare/css/telemedicine.css",
	"/assets/omnexa_healthcare/css/telemedicine-admin.css",
]
web_include_js = [
	"/assets/omnexa_healthcare/js/hospital_website.js?v=20260702",
	"/assets/omnexa_healthcare/js/omnexa-journey.js?v=20260702",
	"/assets/omnexa_healthcare/js/telemedicine-portal.js?v=20260702",
	"/assets/omnexa_healthcare/js/telemedicine-doctor.js?v=20260702",
	"/assets/omnexa_healthcare/js/telemedicine-admin.js?v=20260702",
	"/assets/omnexa_healthcare/js/telemedicine-socket.js?v=20260702",
]

# Registered with omnexa_experience activity website framework
activity_website_packs = [
	{
		"business_activity": "Healthcare",
		"app": "omnexa_healthcare",
		"base_path": "/hospital",
		"site_config_api": "omnexa_healthcare.api.public_hospital_site.get_site_config",
		"nav": [
			{"key": "home", "ar": "الرئيسية", "en": "Home", "href": "/hospital"},
			{"key": "doctors", "ar": "الأطباء", "en": "Doctors", "href": "/hospital/doctors"},
			{"key": "booking", "ar": "احجز موعد", "en": "Book appointment", "href": "/hospital/booking", "cta": True},
		],
	}
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omnexa_healthcare/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# Re-apply healthcare journey shell on department desk pages (after other vertical kits)
page_js = {
	"healthcare-dental-chart": "public/js/omnexa-journey-kit.js",
	"healthcare-lab-workbench": "public/js/omnexa-journey-kit.js",
	"healthcare-radiology-worklist": "public/js/omnexa-journey-kit.js",
}

# include js in doctype views
doctype_js = {
	"Healthcare Patient": "public/js/healthcare_patient.js",
	"Healthcare Service Charge": "public/js/healthcare_service_charge.js",
	"Healthcare Medication Dispense": "public/js/healthcare_medication_dispense.js",
	"Healthcare Appointment": "public/js/healthcare_appointment.js",
	"Healthcare Branch Website": "omnexa_healthcare/doctype/healthcare_branch_website/healthcare_branch_website.js",
	"Healthcare Settings": "public/js/healthcare_settings.js",
}

boot_session = "omnexa_healthcare.healthcare_boot.boot_session"
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
	"Healthcare Companion Stay": "omnexa_healthcare.permissions.healthcare_companion_stay_query_conditions",
	"Healthcare Critical Care Monitoring": "omnexa_healthcare.permissions.healthcare_critical_care_monitoring_query_conditions",
	"Healthcare Blood Donor": "omnexa_healthcare.permissions.healthcare_blood_donor_query_conditions",
	"Healthcare Blood Unit": "omnexa_healthcare.permissions.healthcare_blood_unit_query_conditions",
	"Healthcare Transfusion Order": "omnexa_healthcare.permissions.healthcare_transfusion_order_query_conditions",
	"Healthcare Cssd Instrument": "omnexa_healthcare.permissions.healthcare_cssd_instrument_query_conditions",
	"Healthcare Sterilization Cycle": "omnexa_healthcare.permissions.healthcare_sterilization_cycle_query_conditions",
	"Healthcare Physician Compensation Rule": "omnexa_healthcare.permissions.healthcare_physician_compensation_rule_query_conditions",
	"Healthcare Physician Ledger Entry": "omnexa_healthcare.permissions.healthcare_physician_ledger_entry_query_conditions",
	"Healthcare Physician Settlement": "omnexa_healthcare.permissions.healthcare_physician_settlement_query_conditions",
	"Healthcare Quality Corrective Action": "omnexa_healthcare.permissions.healthcare_quality_corrective_action_query_conditions",
	"Healthcare Infection Surveillance Case": "omnexa_healthcare.permissions.healthcare_infection_surveillance_case_query_conditions",
	"Healthcare Family Unit": "omnexa_healthcare.permissions.healthcare_family_unit_query_conditions",
	"Healthcare Family History": "omnexa_healthcare.permissions.healthcare_family_history_query_conditions",
	"Healthcare Preventive Care Plan": "omnexa_healthcare.permissions.healthcare_preventive_care_plan_query_conditions",
	"Healthcare Family Risk Score": "omnexa_healthcare.permissions.healthcare_family_risk_score_query_conditions",
	"Healthcare Medication Request": "omnexa_healthcare.permissions.healthcare_medication_request_query_conditions",
	"Healthcare Cds Alert Log": "omnexa_healthcare.permissions.healthcare_cds_alert_log_query_conditions",
	"Healthcare Er Visit": "omnexa_healthcare.permissions.healthcare_er_visit_query_conditions",
	"Healthcare Morgue Case": "omnexa_healthcare.permissions.healthcare_morgue_case_query_conditions",
	"Healthcare Pharmacy Substitution Log": "omnexa_healthcare.permissions.healthcare_pharmacy_substitution_log_query_conditions",
	"Healthcare Patient Erasure Request": "omnexa_healthcare.permissions.healthcare_patient_erasure_request_query_conditions",
	"Healthcare Telemedicine Session": "omnexa_healthcare.permissions.healthcare_telemedicine_session_query_conditions",
	"Healthcare Telemedicine Configuration": "omnexa_healthcare.permissions.healthcare_telemedicine_configuration_query_conditions",
	"Healthcare Telemedicine Consent": "omnexa_healthcare.permissions.healthcare_telemedicine_consent_query_conditions",
	"Healthcare Remote Monitoring Device": "omnexa_healthcare.permissions.healthcare_remote_monitoring_device_query_conditions",
	"Healthcare Remote Monitoring Reading": "omnexa_healthcare.permissions.healthcare_remote_monitoring_reading_query_conditions",
	"Healthcare Telemedicine Queue": "omnexa_healthcare.permissions.healthcare_telemedicine_queue_query_conditions",
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

doc_events = {
	"Healthcare Telemedicine Session": {
		"on_update": "omnexa_healthcare.api.telemedicine.on_session_update",
		"after_insert": "omnexa_healthcare.api.telemedicine.on_session_create",
	},
	"Healthcare Remote Monitoring Reading": {
		"after_insert": "omnexa_healthcare.api.telemedicine_monitoring.on_reading_create",
	},
}

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
	"Healthcare Morgue Case",
	"Healthcare In Basket Item",
	"Healthcare Adt Transfer",
	"Healthcare Companion Stay",
	"Healthcare Critical Care Monitoring",
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
	"Healthcare Blood Donor",
	"Healthcare Blood Unit",
	"Healthcare Transfusion Order",
	"Healthcare Cssd Instrument",
	"Healthcare Sterilization Cycle",
	"Healthcare Physician Compensation Rule",
	"Healthcare Physician Settlement",
	"Healthcare Quality Corrective Action",
	"Healthcare Infection Surveillance Case",
	"Healthcare Family Unit",
	"Healthcare Family History",
	"Healthcare Preventive Care Plan",
	"Healthcare Family Risk Score",
	"Healthcare Medication Request",
	"Healthcare Cds Alert Log",
	"Healthcare Pharmacy Substitution Log",
	"Healthcare Patient Erasure Request",
	"Healthcare Telemedicine Session",
	"Healthcare Telemedicine Consent",
	"Healthcare Remote Monitoring Device",
	"Healthcare Remote Monitoring Reading",
	"Healthcare Telemedicine Queue",
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
doc_events["Healthcare Telemedicine Session"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Telemedicine Session"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Telemedicine Consent"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Telemedicine Consent"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Remote Monitoring Device"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Remote Monitoring Device"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Remote Monitoring Reading"]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
doc_events["Healthcare Remote Monitoring Reading"]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"

from omnexa_healthcare.gap_closure_wave9_defs import PHI_AUDIT_DOCTYPES as _PHI_AUDIT_DOCTYPES

for _phi_dt in _PHI_AUDIT_DOCTYPES:
	if _phi_dt in ("Healthcare Patient", "Healthcare Encounter"):
		continue
	doc_events.setdefault(_phi_dt, {})
	if isinstance(doc_events[_phi_dt], dict):
		doc_events[_phi_dt]["after_insert"] = "omnexa_healthcare.api.audit_phi.log_phi_access"
		doc_events[_phi_dt]["on_update"] = "omnexa_healthcare.api.audit_phi.log_phi_access"

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
before_request = [
	"omnexa_healthcare.license_gate.before_request",
	"omnexa_healthcare.healthcare_mfa.validate_phi_role_mfa",
]
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

# Website Routes
# --------------
website_routes = [
	{"from_route": "/telemedicine", "to_route": "telemedicine"},
	{"from_route": "/telemedicine-doctor", "to_route": "telemedicine-doctor"},
	{"from_route": "/telemedicine-admin", "to_route": "telemedicine-admin"},
]

