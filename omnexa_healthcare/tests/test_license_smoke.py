from frappe.tests.utils import FrappeTestCase

from omnexa_healthcare import hooks, license_gate


class TestHealthcareLicenseSmoke(FrappeTestCase):
	def test_license_gate_is_wired(self):
		self.assertEqual(hooks.before_request, ["omnexa_healthcare.license_gate.before_request"])
		self.assertEqual(license_gate._APP, "omnexa_healthcare")
