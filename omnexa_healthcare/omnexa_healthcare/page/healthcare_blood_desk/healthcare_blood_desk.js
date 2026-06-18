frappe.pages["healthcare-blood-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Blood Bank"),
		titleAr: "بنك الدم",
		titleEn: "Blood Bank",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "nurse",
		api: "omnexa_healthcare.api.specialty_desks.get_blood_bank_dashboard",
		rowsField: "units",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "unit_number", "ar": "الوحدة", "en": "Unit"}, {"field": "blood_group", "ar": "الفصيلة", "en": "Group"}, {"field": "component", "ar": "المكون", "en": "Component"}, {"field": "expiry_date", "ar": "الانتهاء", "en": "Expiry"}],
		links: [],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
