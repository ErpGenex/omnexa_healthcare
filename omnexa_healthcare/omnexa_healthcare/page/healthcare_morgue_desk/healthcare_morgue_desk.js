frappe.pages["healthcare-morgue-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Morgue Desk"),
		titleAr: "المشرحة",
		titleEn: "Morgue Desk",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "nurse",
		api: "omnexa_healthcare.api.specialty_desks.get_morgue_dashboard",
		rowsField: "cases",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "name", "ar": "المرجع", "en": "Ref"}, {"field": "patient", "ar": "المريض", "en": "Patient"}, {"field": "status", "ar": "الحالة", "en": "Status"}],
		links: [],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
