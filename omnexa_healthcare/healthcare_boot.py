# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from omnexa_healthcare.healthcare_mfa import apply_mfa_boot_policy, validate_phi_role_mfa
from omnexa_healthcare.terminology import apply_boot_terminology


def boot_session(bootinfo) -> None:
	apply_boot_terminology(bootinfo)
	apply_mfa_boot_policy(bootinfo)
	try:
		validate_phi_role_mfa()
	except Exception:
		pass
