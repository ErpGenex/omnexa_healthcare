frappe.pages["healthcare-optometry-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Optometry Desk"),
		titleAr: "البصريات",
		titleEn: "Optometry Desk",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "physician",
		api: "omnexa_healthcare.api.specialty_desks.get_optometry_dashboard",
		rowsField: "orders",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [{"field": "name", "ar": "المرجع", "en": "Ref"}, {"field": "patient", "ar": "المريض", "en": "Patient"}, {"field": "status", "ar": "الحالة", "en": "Status"}],
		links: [],
		homeRoute: "/app/healthcare-workcenter",
	});
};
