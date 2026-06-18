frappe.pages["healthcare-ot-board"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("OT Board"),
		titleAr: "غرف العمليات",
		titleEn: "OT Board",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "nurse",
		api: "omnexa_healthcare.api.specialty_desks.get_ot_board",
		rowsField: "cases",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "name", "ar": "المرجع", "en": "Ref"}, {"field": "patient", "ar": "المريض", "en": "Patient"}, {"field": "status", "ar": "الحالة", "en": "Status"}],
		links: [],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
