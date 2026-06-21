/* Healthcare activity: Customer → Patient everywhere in Desk UI */
(function () {
	function healthcareMode() {
		return Boolean(frappe.boot && frappe.boot.omnexa_healthcare_mode);
	}

	function hiddenDoctypes() {
		return new Set((frappe.boot && frappe.boot.omnexa_hidden_doctypes) || []);
	}

	function terminologyMap() {
		return Object.assign({}, (frappe.boot && frappe.boot.omnexa_patient_terminology) || {});
	}

	function translateTerm(text) {
		if (!healthcareMode() || text == null) return text;
		const key = String(text);
		const map = terminologyMap();
		return map[key] || map[key.trim()] || text;
	}

	function applyMessageOverrides() {
		const map = terminologyMap();
		if (!Object.keys(map).length) return;
		frappe._messages = Object.assign({}, frappe._messages || {}, map);
	}

	function patchTranslation() {
		if (frappe.__omnexa_healthcare_translation_patched) return;
		const orig = frappe._;
		frappe._ = function (txt, args, context) {
			const out = orig.call(this, translateTerm(txt), args, context);
			if (typeof out === "string" && healthcareMode()) {
				return translateTerm(out);
			}
			return out;
		};
		frappe.__omnexa_healthcare_translation_patched = true;
	}

	function patchDoctypeLabels() {
		if (!healthcareMode() || !frappe.boot.docs) return;
		const map = terminologyMap();
		frappe.boot.docs.forEach((d) => {
			if (d.name === "Customer" && map["Customer"]) {
				d.label = map["Customer"];
			}
		});
	}

	function patchRoutes() {
		if (frappe.__omnexa_healthcare_route_patched) return;
		const orig = frappe.set_route;
		frappe.set_route = function () {
			const args = Array.from(arguments);
			if (healthcareMode()) {
				if (args[0] === "List" && args[1] === "Customer") {
					args[1] = "Healthcare Patient";
				}
				if (args[0] === "Form" && args[1] === "Customer") {
					args[1] = "Healthcare Patient";
					args[2] = args[2] || "new";
				}
			}
			return orig.apply(this, args);
		};
		frappe.__omnexa_healthcare_route_patched = true;
	}

	function patchLinkFilters() {
		const hidden = hiddenDoctypes();
		if (!hidden.size) return;
		const orig = frappe.ui.form.ControlLink.prototype.get_query;
		if (orig.__omnexa_healthcare_patched) return;
		frappe.ui.form.ControlLink.prototype.get_query = function () {
			const query = orig.apply(this, arguments) || {};
			if (!healthcareMode()) return query;
			if (hidden.has(this.df.options)) {
				query.filters = Object.assign({}, query.filters, { name: ["=", "__none__"] });
			}
			if (this.df.fieldname === "customer" && this.df.options === "Customer") {
				this.df.label = translateTerm(this.df.label || "Customer");
			}
			return query;
		};
		frappe.ui.form.ControlLink.prototype.get_query.__omnexa_healthcare_patched = true;
	}

	function hideWorkspaceCustomerLinks() {
		if (!healthcareMode()) return;
		const hidden = hiddenDoctypes();
		const hide = () => {
			hidden.forEach((dt) => {
				$(`.sidebar-item-container[data-link-type="DocType"][data-link-to="${dt}"]`).hide();
			});
			$('[data-label="Customer"], [data-label="Customers"]').closest(".sidebar-item-container").hide();
		};
		$(document).on("app_ready workspace_sidebar_updated", hide);
		hide();
	}

	function patchBranchDemoLabels() {
		frappe.ui.form.on("Branch", {
			refresh(frm) {
				if (!healthcareMode() && frm.doc.branch_demo_activity !== "Healthcare") return;
				const map = {
					branch_demo_customers: __("Patients"),
				};
				Object.entries(map).forEach(([fieldname, label]) => {
					if (frm.fields_dict[fieldname]) {
						frm.fields_dict[fieldname].set_label(label);
					}
				});
			},
		});
	}

	function patchFormCustomerFields(frm) {
		if (!healthcareMode() || !frm || !frm.fields_dict) return;
		Object.values(frm.fields_dict).forEach((field) => {
			if (!field || !field.df) return;
			if (field.df.options === "Customer" || field.df.fieldname === "customer") {
				const lbl = field.df.label || "Customer";
				field.set_label(translateTerm(lbl));
			}
			if (field.df.fieldname === "party_type" && field.df.options && field.df.options.includes("Customer")) {
				field.df.options = field.df.options.replace(/Customer/g, "Patient");
			}
		});
	}

	frappe.ui.form.on("*", {
		refresh(frm) {
			patchFormCustomerFields(frm);
		},
	});

	frappe.ready(function () {
		if (!healthcareMode()) return;
		applyMessageOverrides();
		try {
			const map = Object.assign({}, terminologyMap(), (frappe.boot && frappe.boot.__messages) || {});
			if (Object.keys(map).length) {
				frappe._messages = Object.assign({}, frappe._messages || {}, map);
			}
		} catch (e) {
			/* ignore */
		}
		patchTranslation();
		patchDoctypeLabels();
		patchRoutes();
		patchLinkFilters();
		hideWorkspaceCustomerLinks();
		patchBranchDemoLabels();
	});
})();
