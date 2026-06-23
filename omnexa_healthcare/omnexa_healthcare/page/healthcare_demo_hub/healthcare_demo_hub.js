/** Legacy route — redirects to Healthcare Workcenter */
frappe.pages["healthcare-demo-hub"].on_page_load = function () {
	window.location.replace("/app/healthcare-workcenter");
};
