# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""DocType definitions for Wave 6 — Family Medicine Center of Excellence."""

from __future__ import annotations

GAP_CLOSURE_WAVE6_DOCTYPES: list[dict] = [
	{
		"name": "Healthcare Family Member",
		"istable": True,
		"autoname": "hash",
		"fields": [
			("patient", "Link", "Patient", {"options": "Healthcare Patient", "reqd": 1, "in_list_view": 1}),
			(
				"relationship",
				"Select",
				"Relationship",
				{
					"options": "Head\nSpouse\nChild\nParent\nSibling\nGrandparent\nGrandchild\nOther",
					"reqd": 1,
					"in_list_view": 1,
				},
			),
			("is_primary_contact", "Check", "Primary contact", {"default": "0", "in_list_view": 1}),
			("enrollment_date", "Date", "Enrollment date"),
			("notes", "Small Text", "Notes"),
		],
	},
	{
		"name": "Healthcare Preventive Care Item",
		"istable": True,
		"autoname": "hash",
		"fields": [
			("screening_name", "Data", "Screening / service", {"reqd": 1, "in_list_view": 1}),
			("due_date", "Date", "Due date", {"in_list_view": 1}),
			(
				"status",
				"Select",
				"Status",
				{"options": "Due\nScheduled\nCompleted\nOverdue\nWaived", "default": "Due", "in_list_view": 1},
			),
			("completed_date", "Date", "Completed date"),
			("notes", "Small Text", "Notes"),
		],
	},
	{
		"name": "Healthcare Family Unit",
		"autoname": "naming_series:",
		"naming_series": "HFU-.#####",
		"fields": [
			("naming_series", "Select", "Series", {"options": "HFU-.#####", "reqd": 1, "default": "HFU-.#####"}),
			("family_number", "Data", "Family number", {"reqd": 1, "unique": 1, "in_list_view": 1}),
			("family_name", "Data", "Family name", {"reqd": 1, "in_list_view": 1}),
			("head_of_family", "Link", "Head of family", {"options": "Healthcare Patient", "reqd": 1, "in_list_view": 1}),
			("primary_care_practitioner", "Link", "Family physician", {"options": "Healthcare Practitioner", "in_list_view": 1}),
			(
				"household_status",
				"Select",
				"Household status",
				{"options": "Active\nInactive\nRelocated\nDissolved", "default": "Active", "in_list_view": 1},
			),
			("shared_genetic_risk_notes", "Small Text", "Shared genetic / hereditary notes"),
			("members", "Table", "Family members", {"options": "Healthcare Family Member", "reqd": 1}),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch", "reqd": 1}),
		],
	},
	{
		"name": "Healthcare Family History",
		"autoname": "naming_series:",
		"naming_series": "HFH-.#####",
		"fields": [
			("naming_series", "Select", "Series", {"options": "HFH-.#####", "reqd": 1, "default": "HFH-.#####"}),
			("family_unit", "Link", "Family unit", {"options": "Healthcare Family Unit", "reqd": 1, "in_list_view": 1}),
			("patient", "Link", "Member patient", {"options": "Healthcare Patient", "in_list_view": 1}),
			(
				"condition_category",
				"Select",
				"Category",
				{
					"options": "Diabetes\nHypertension\nHeart Disease\nCancer\nGenetic Disorder\nPsychiatric\nChronic Other",
					"reqd": 1,
					"in_list_view": 1,
				},
			),
			("condition_description", "Data", "Condition", {"reqd": 1, "in_list_view": 1}),
			("icd10_code", "Data", "ICD-10"),
			("icd11_code", "Data", "ICD-11"),
			("snomed_code", "Data", "SNOMED"),
			("relative_relationship", "Select", "Relative", {"options": "Self\nFather\nMother\nSibling\nChild\nGrandparent\nOther", "reqd": 1}),
			("age_at_onset", "Int", "Age at onset"),
			("notes", "Small Text", "Notes"),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch", "reqd": 1}),
		],
	},
	{
		"name": "Healthcare Preventive Care Plan",
		"autoname": "naming_series:",
		"naming_series": "HPC-.#####",
		"fields": [
			("naming_series", "Select", "Series", {"options": "HPC-.#####", "reqd": 1, "default": "HPC-.#####"}),
			("family_unit", "Link", "Family unit", {"options": "Healthcare Family Unit", "in_list_view": 1}),
			("patient", "Link", "Patient", {"options": "Healthcare Patient", "in_list_view": 1}),
			("plan_title", "Data", "Plan title", {"reqd": 1, "in_list_view": 1}),
			("status", "Select", "Status", {"options": "Draft\nActive\nCompleted\nCancelled", "default": "Active", "in_list_view": 1}),
			("start_date", "Date", "Start date", {"reqd": 1}),
			("end_date", "Date", "End date"),
			("practitioner", "Link", "Practitioner", {"options": "Healthcare Practitioner"}),
			("items", "Table", "Preventive items", {"options": "Healthcare Preventive Care Item"}),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch", "reqd": 1}),
		],
	},
	{
		"name": "Healthcare Family Risk Score",
		"autoname": "naming_series:",
		"naming_series": "HRS-.#####",
		"fields": [
			("naming_series", "Select", "Series", {"options": "HRS-.#####", "reqd": 1, "default": "HRS-.#####"}),
			("family_unit", "Link", "Family unit", {"options": "Healthcare Family Unit", "reqd": 1, "in_list_view": 1}),
			("patient", "Link", "Patient", {"options": "Healthcare Patient", "in_list_view": 1}),
			("assessment_date", "Date", "Assessment date", {"reqd": 1, "in_list_view": 1, "default": "Today"}),
			("cardiovascular_risk_score", "Int", "Cardiovascular risk %", {"in_list_view": 1}),
			("diabetes_risk_score", "Int", "Diabetes risk %", {"in_list_view": 1}),
			(
				"overall_risk_level",
				"Select",
				"Overall risk",
				{"options": "Low\nMedium\nHigh\nCritical", "default": "Low", "in_list_view": 1},
			),
			("risk_factors_json", "Long Text", "Risk factors (JSON)"),
			("recommendations", "Text", "Recommendations"),
			("computed_by", "Link", "Computed by", {"options": "User"}),
			("company", "Link", "Company", {"options": "Company", "reqd": 1}),
			("branch", "Link", "Branch", {"options": "Branch", "reqd": 1}),
		],
	},
]
