import frappe


SUPPORTED_FRAPPE_MAJOR = 15


def enforce_supported_frappe_version():
	"""Fail fast when running on unsupported Frappe major versions."""
	version_text = (getattr(frappe, "__version__", "") or "").strip()
	if not version_text:
		return

	major_token = version_text.split(".", 1)[0]
	try:
		major = int(major_token)
	except ValueError:
		return

	if major != SUPPORTED_FRAPPE_MAJOR:
		frappe.throw(
			f"Unsupported Frappe version '{version_text}' for omnexa_healthcare. "
			"Supported range is >=15.0,<16.0.",
			frappe.ValidationError,
		)


def after_migrate():
	try:
		from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace_menu

		sync_healthcare_workspace_menu(save=True, rebuild=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa Healthcare: workspace sync failed")

	try:
		from omnexa_healthcare.patches.v1_0.sync_healthcare_report_roles import execute as sync_report_roles

		sync_report_roles()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa Healthcare: report role sync failed")

	try:
		from omnexa_healthcare.patches.v1_0.sync_lab_print_format import execute as sync_lab_print

		sync_lab_print()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa Healthcare: lab print format sync failed")
