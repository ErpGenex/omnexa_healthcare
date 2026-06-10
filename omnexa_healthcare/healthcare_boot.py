# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from omnexa_healthcare.terminology import apply_boot_terminology


def boot_session(bootinfo) -> None:
	apply_boot_terminology(bootinfo)
