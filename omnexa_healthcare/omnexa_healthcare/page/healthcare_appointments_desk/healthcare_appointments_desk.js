frappe.pages["healthcare-appointments-desk"].on_page_load = function (wrapper) {
	omnexa_healthcare.portal.mount(wrapper, {
		deskTitle: __("Appointments"),
		titleAr: "المواعيد",
		titleEn: "Appointments",
		roleAr: "Omnexa Healthcare",
		roleEn: "Omnexa Healthcare",
		sidebarRole: "reception",
		api: "omnexa_healthcare.api.specialty_desks.get_appointments_directory",
		rowsField: "appointments",
		tableTitleAr: "البيانات",
		tableTitleEn: "Records",
		columns: [
			{ field: "name", ar: "الموعد", en: "Appointment" },
			{ field: "patient_display", ar: "المريض", en: "Patient" },
			{ field: "practitioner", ar: "الطبيب", en: "Doctor" },
			{ field: "appointment_date", ar: "التاريخ", en: "Date" },
			{ field: "status", ar: "الحالة", en: "Status" },
		],
		links: [
			{ labelAr: "موعد جديد", labelEn: "New Appointment", route: "/app/healthcare-appointment/new-healthcare-appointment-1", icon: "➕" },
			{ labelAr: "التقويم", labelEn: "Calendar", route: "/app/healthcare-appointment-calendar", icon: "🗓" },
		],
		homeRoute: "/app/healthcare-demo-hub",
	});
};
