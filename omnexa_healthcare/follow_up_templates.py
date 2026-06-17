# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Default multi-visit follow-up plan templates per specialty module."""

from __future__ import annotations

FOLLOW_UP_PLAN_TEMPLATES: dict[str, dict] = {
	"orthopedics": {
		"supports_multi_visit": True,
		"default_plan_type": "rehabilitation",
		"plan_types": ["rehabilitation", "post_op"],
		"templates": {
			"rehabilitation": {
				"plan_title": "Orthopedic rehabilitation program",
				"visits": [
					{"visit_objective": "Initial assessment & imaging review", "offset_days": 0},
					{"visit_objective": "ROM assessment & exercise plan", "offset_days": 14},
					{"visit_objective": "Strength & mobility progress", "offset_days": 28},
					{"visit_objective": "Functional capacity review", "offset_days": 56},
					{"visit_objective": "Discharge & home program", "offset_days": 84},
				],
			},
			"post_op": {
				"plan_title": "Post-operative orthopedic follow-up",
				"visits": [
					{"visit_objective": "Day 7 wound check", "offset_days": 7},
					{"visit_objective": "Day 14 suture review", "offset_days": 14},
					{"visit_objective": "Week 6 weight-bearing review", "offset_days": 42},
					{"visit_objective": "Week 12 final review", "offset_days": 84},
				],
			},
		},
	},
	"gynecology": {
		"supports_multi_visit": True,
		"default_plan_type": "antenatal",
		"plan_types": ["antenatal", "postnatal"],
		"templates": {
			"antenatal": {
				"plan_title": "Antenatal care schedule",
				"visits": [
					{"visit_objective": "Booking visit & baseline labs", "offset_days": 0},
					{"visit_objective": "12-week dating scan", "offset_days": 28},
					{"visit_objective": "20-week anomaly scan", "offset_days": 70},
					{"visit_objective": "28-week review & glucose screen", "offset_days": 112},
					{"visit_objective": "32-week growth scan", "offset_days": 140},
					{"visit_objective": "36-week birth plan", "offset_days": 168},
					{"visit_objective": "38-week cervical assessment", "offset_days": 182},
					{"visit_objective": "40-week delivery planning", "offset_days": 196},
				],
			},
			"postnatal": {
				"plan_title": "Postnatal follow-up schedule",
				"visits": [
					{"visit_objective": "Day 7 postpartum check", "offset_days": 7},
					{"visit_objective": "Week 6 postpartum review", "offset_days": 42},
					{"visit_objective": "Contraception & recovery review", "offset_days": 84},
				],
			},
		},
	},
	"dental": {
		"supports_multi_visit": True,
		"default_plan_type": "dental",
		"plan_types": ["dental"],
		"templates": {
			"dental": {
				"plan_title": "Dental restorative treatment plan",
				"visits": [
					{"visit_objective": "Exam, X-ray & treatment planning", "offset_days": 0},
					{"visit_objective": "Restorative procedure visit 1", "offset_days": 7},
					{"visit_objective": "Restorative procedure visit 2", "offset_days": 21},
					{"visit_objective": "Final review & preventive care", "offset_days": 42},
				],
			},
		},
	},
	"physiotherapy": {
		"supports_multi_visit": True,
		"default_plan_type": "physiotherapy",
		"plan_types": ["physiotherapy", "rehabilitation"],
		"templates": {
			"physiotherapy": {
				"plan_title": "Physiotherapy treatment course",
				"visits": [
					{"visit_objective": "Initial assessment", "offset_days": 0},
					{"visit_objective": "Treatment session 1", "offset_days": 3},
					{"visit_objective": "Treatment session 2", "offset_days": 7},
					{"visit_objective": "Treatment session 3", "offset_days": 14},
					{"visit_objective": "Re-assessment & home program", "offset_days": 21},
				],
			},
			"rehabilitation": {
				"plan_title": "Physiotherapy rehabilitation program",
				"visits": [
					{"visit_objective": "Functional mobility assessment", "offset_days": 0},
					{"visit_objective": "Strength & ROM session", "offset_days": 7},
					{"visit_objective": "Gait & balance progress", "offset_days": 21},
					{"visit_objective": "Home exercise program review", "offset_days": 42},
				],
			},
		},
	},
	"oncology": {
		"supports_multi_visit": True,
		"default_plan_type": "chemotherapy",
		"plan_types": ["chemotherapy", "chronic_care"],
		"templates": {
			"chemotherapy": {
				"plan_title": "Chemotherapy cycle follow-up",
				"visits": [
					{"visit_objective": "Cycle 1 pre-treatment review", "offset_days": 0},
					{"visit_objective": "Cycle 1 toxicity review", "offset_days": 7},
					{"visit_objective": "Cycle 2 pre-treatment review", "offset_days": 21},
					{"visit_objective": "Cycle 2 toxicity review", "offset_days": 28},
					{"visit_objective": "Mid-treatment imaging review", "offset_days": 42},
				],
			},
			"chronic_care": {
				"plan_title": "Oncology survivorship follow-up",
				"visits": [
					{"visit_objective": "Survivorship assessment", "offset_days": 0},
					{"visit_objective": "3-month symptom review", "offset_days": 90},
					{"visit_objective": "6-month labs & imaging review", "offset_days": 180},
				],
			},
		},
	},
	"cardiology": {
		"supports_multi_visit": True,
		"default_plan_type": "chronic_care",
		"plan_types": ["chronic_care", "post_op"],
		"templates": {
			"chronic_care": {
				"plan_title": "Cardiac chronic care follow-up",
				"visits": [
					{"visit_objective": "Baseline cardiac review & labs", "offset_days": 0},
					{"visit_objective": "4-week medication titration", "offset_days": 28},
					{"visit_objective": "3-month echo & review", "offset_days": 90},
					{"visit_objective": "6-month comprehensive review", "offset_days": 180},
				],
			},
			"post_op": {
				"plan_title": "Cardiac post-procedure follow-up",
				"visits": [
					{"visit_objective": "Week 1 wound & vitals check", "offset_days": 7},
					{"visit_objective": "Week 4 medication review", "offset_days": 28},
					{"visit_objective": "Week 8 cardiac rehab clearance", "offset_days": 56},
				],
			},
		},
	},
	"psychiatry": {
		"supports_multi_visit": True,
		"default_plan_type": "psychotherapy",
		"plan_types": ["psychotherapy", "chronic_care"],
		"templates": {
			"psychotherapy": {
				"plan_title": "Psychiatric follow-up course",
				"visits": [
					{"visit_objective": "Initial psychiatric assessment", "offset_days": 0},
					{"visit_objective": "Medication review week 2", "offset_days": 14},
					{"visit_objective": "Therapy session week 4", "offset_days": 28},
					{"visit_objective": "8-week outcome review", "offset_days": 56},
				],
			},
			"chronic_care": {
				"plan_title": "Psychiatric chronic care maintenance",
				"visits": [
					{"visit_objective": "Medication stability review", "offset_days": 0},
					{"visit_objective": "6-week follow-up", "offset_days": 42},
					{"visit_objective": "3-month outcome review", "offset_days": 90},
				],
			},
		},
	},
	"pediatrics": {
		"supports_multi_visit": True,
		"default_plan_type": "chronic_care",
		"plan_types": ["chronic_care"],
		"templates": {
			"chronic_care": {
				"plan_title": "Pediatric growth & immunization follow-up",
				"visits": [
					{"visit_objective": "Well-child visit & growth chart", "offset_days": 0},
					{"visit_objective": "Immunization catch-up review", "offset_days": 30},
					{"visit_objective": "3-month developmental check", "offset_days": 90},
					{"visit_objective": "6-month comprehensive review", "offset_days": 180},
				],
			},
		},
	},
	"surgery": {
		"supports_multi_visit": True,
		"default_plan_type": "post_op",
		"plan_types": ["post_op"],
		"templates": {
			"post_op": {
				"plan_title": "Surgical post-operative follow-up",
				"visits": [
					{"visit_objective": "Day 3 post-op review", "offset_days": 3},
					{"visit_objective": "Day 10 wound review", "offset_days": 10},
					{"visit_objective": "Week 4 recovery check", "offset_days": 28},
					{"visit_objective": "Week 8 final surgical review", "offset_days": 56},
				],
			},
		},
	},
	"dermatology": {
		"supports_multi_visit": True,
		"default_plan_type": "dermatology_course",
		"plan_types": ["dermatology_course"],
		"templates": {
			"dermatology_course": {
				"plan_title": "Dermatology treatment course",
				"visits": [
					{"visit_objective": "Lesion assessment & biopsy plan", "offset_days": 0},
					{"visit_objective": "Treatment session 1", "offset_days": 14},
					{"visit_objective": "Treatment session 2", "offset_days": 28},
					{"visit_objective": "Response review", "offset_days": 42},
				],
			},
		},
	},
	"neurology": {
		"supports_multi_visit": True,
		"default_plan_type": "chronic_care",
		"plan_types": ["chronic_care"],
		"templates": {
			"chronic_care": {
				"plan_title": "Neurology chronic follow-up",
				"visits": [
					{"visit_objective": "Neurological baseline assessment", "offset_days": 0},
					{"visit_objective": "6-week symptom review", "offset_days": 42},
					{"visit_objective": "3-month MRI & medication review", "offset_days": 90},
				],
			},
		},
	},
	"gastroenterology": {
		"supports_multi_visit": True,
		"default_plan_type": "chronic_care",
		"plan_types": ["chronic_care", "post_op"],
		"templates": {
			"chronic_care": {
				"plan_title": "GI disease follow-up schedule",
				"visits": [
					{"visit_objective": "Initial GI assessment", "offset_days": 0},
					{"visit_objective": "Post-endoscopy review", "offset_days": 14},
					{"visit_objective": "3-month symptom & labs review", "offset_days": 90},
				],
			},
			"post_op": {
				"plan_title": "Post-procedure GI follow-up",
				"visits": [
					{"visit_objective": "Day 3 post-procedure check", "offset_days": 3},
					{"visit_objective": "Week 2 symptom review", "offset_days": 14},
					{"visit_objective": "Week 6 diet & recovery review", "offset_days": 42},
				],
			},
		},
	},
	"ophthalmology": {
		"supports_multi_visit": True,
		"default_plan_type": "post_op",
		"plan_types": ["post_op"],
		"templates": {
			"post_op": {
				"plan_title": "Ophthalmology post-procedure follow-up",
				"visits": [
					{"visit_objective": "Day 1 post-procedure check", "offset_days": 1},
					{"visit_objective": "Week 1 visual acuity review", "offset_days": 7},
					{"visit_objective": "Month 1 final review", "offset_days": 30},
				],
			},
		},
	},
	"urology": {
		"supports_multi_visit": True,
		"default_plan_type": "post_op",
		"plan_types": ["post_op", "chronic_care"],
		"templates": {
			"post_op": {
				"plan_title": "Urology post-procedure follow-up",
				"visits": [
					{"visit_objective": "Catheter removal review", "offset_days": 7},
					{"visit_objective": "4-week recovery check", "offset_days": 28},
				],
			},
			"chronic_care": {
				"plan_title": "Urology chronic care follow-up",
				"visits": [
					{"visit_objective": "Initial urology assessment", "offset_days": 0},
					{"visit_objective": "3-month labs review", "offset_days": 90},
					{"visit_objective": "6-month comprehensive review", "offset_days": 180},
				],
			},
		},
	},
}

MULTI_VISIT_MODULE_CODES: frozenset[str] = frozenset(
	code for code, spec in FOLLOW_UP_PLAN_TEMPLATES.items() if spec.get("supports_multi_visit")
)
