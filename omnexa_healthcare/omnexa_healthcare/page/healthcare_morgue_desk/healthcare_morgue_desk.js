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
		columns: [
			{ field: "name", ar: "المرجع", en: "Ref" },
			{ field: "body_tag", ar: "رقم الجثمان", en: "Body Tag" },
			{ field: "patient_name", ar: "المريض", en: "Patient" },
			{ field: "status", ar: "الحالة", en: "Status" },
			{ field: "storage_location", ar: "الموقع", en: "Location" },
		],
		kpis: [
			{ field: "open_count", labelAr: "حالات مفتوحة", labelEn: "Open Cases" },
		],
		links: [
			{ label: __("Morgue Cases"), route: "List/Healthcare Morgue Case", icon: "⚰️" },
		],
		homeRoute: "/app/healthcare-workcenter",
	});
};
