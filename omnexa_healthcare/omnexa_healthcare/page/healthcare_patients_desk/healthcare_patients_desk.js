frappe.pages["healthcare-patients-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Patients"),
		titleAr: "دليل المرضى",
		titleEn: "Patients",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "reception",
		api: "omnexa_healthcare.api.specialty_desks.get_patients_directory",
		rowsField: "patients",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [
			{ field: "name", ar: "MRN", en: "MRN" },
			{ field: "full_name", ar: "الاسم", en: "Name" },
			{ field: "mobile", ar: "الجوال", en: "Mobile" },
			{ field: "gender", ar: "النوع", en: "Gender" },
		],
		links: [
			{ labelAr: "مريض جديد", labelEn: "New Patient", route: "/app/healthcare-patient/new-healthcare-patient-1", icon: "➕" },
			{ labelAr: "الاستقبال", labelEn: "Reception", route: "/app/healthcare-reception-desk", icon: "🏥" },
		],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
