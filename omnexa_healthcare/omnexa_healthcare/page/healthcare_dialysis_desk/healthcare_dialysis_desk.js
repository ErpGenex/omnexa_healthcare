frappe.pages["healthcare-dialysis-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Dialysis Desk"),
		titleAr: "غسيل الكلى",
		titleEn: "Dialysis Desk",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "nurse",
		api: "omnexa_healthcare.api.specialty_desks.get_dialysis_dashboard",
		rowsField: "sessions",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "name", "ar": "المرجع", "en": "Ref"}, {"field": "patient", "ar": "المريض", "en": "Patient"}, {"field": "status", "ar": "الحالة", "en": "Status"}],
		links: [],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
