frappe.pages["healthcare-ld-board"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("L&D Board"),
		titleAr: "الولادة",
		titleEn: "L&D Board",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "nurse",
		api: "omnexa_healthcare.api.specialty_desks.get_ld_board_dashboard",
		rowsField: "cases",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "name", "ar": "المرجع", "en": "Ref"}, {"field": "patient", "ar": "المريض", "en": "Patient"}, {"field": "status", "ar": "الحالة", "en": "Status"}],
		links: [],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
