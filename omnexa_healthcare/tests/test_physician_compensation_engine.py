# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import unittest

from omnexa_healthcare.api.physician_compensation_engine import CompensationTier, calculate_physician_share


class TestPhysicianCompensationEngine(unittest.TestCase):
	def test_revenue_share_gross_hospital_absorbs_discount(self):
		tier = CompensationTier(
			service_category="Consultation",
			share_percent=40,
			fixed_amount=0,
			calculation_base="Gross",
			discount_handling="Hospital Absorbs Discount",
			physician_discount_share_percent=0,
			min_physician_share=0,
			max_physician_share=0,
		)
		out = calculate_physician_share(500, 100, tier)
		self.assertEqual(out["physician_share"], 200)
		self.assertEqual(out["hospital_share"], 200)

	def test_physician_absorbs_discount(self):
		tier = CompensationTier(
			service_category="Surgery",
			share_percent=50,
			fixed_amount=0,
			calculation_base="Gross",
			discount_handling="Physician Absorbs Discount",
			physician_discount_share_percent=0,
			min_physician_share=0,
			max_physician_share=0,
		)
		out = calculate_physician_share(10000, 2000, tier)
		self.assertEqual(out["physician_share"], 3000)

	def test_split_discount(self):
		tier = CompensationTier(
			service_category="Procedure",
			share_percent=30,
			fixed_amount=0,
			calculation_base="Gross",
			discount_handling="Split Discount",
			physician_discount_share_percent=50,
			min_physician_share=0,
			max_physician_share=0,
		)
		out = calculate_physician_share(1000, 200, tier)
		self.assertEqual(out["physician_share"], 200)

	def test_fixed_physician_amount(self):
		tier = CompensationTier(
			service_category="Follow-up",
			share_percent=0,
			fixed_amount=150,
			calculation_base="Gross",
			discount_handling="Fixed Physician Amount",
			physician_discount_share_percent=0,
			min_physician_share=0,
			max_physician_share=0,
		)
		out = calculate_physician_share(500, 50, tier)
		self.assertEqual(out["physician_share"], 150)
