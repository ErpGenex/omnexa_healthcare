frappe.pages["healthcare-family-tree"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Family Medical Tree (Genogram)"),
		single_column: true,
	});
	const $root = $(`<div></div>`).appendTo(page.body);
	const $filters = $(`<div class="row mb-3"></div>`).appendTo($root);
	const familyUnit = frappe.ui.form.make_control({
		parent: $filters,
		df: { fieldtype: "Link", options: "Healthcare Family Unit", label: __("Family unit"), reqd: 1 },
		render_input: true,
	});
	const $canvas = $(`<div id="hc-family-tree-canvas" class="border rounded p-4 bg-light" style="min-height:360px"></div>`).appendTo($root);

	const routeOpts = frappe.route_options || {};
	if (routeOpts.family_unit) {
		setTimeout(() => {
			familyUnit.set_value(routeOpts.family_unit);
			loadTree();
		}, 300);
	}

	const categoryColor = {
		Diabetes: "#e67e22",
		Hypertension: "#3498db",
		"Heart Disease": "#e74c3c",
		Cancer: "#9b59b6",
		"Genetic Disorder": "#1abc9c",
		Psychiatric: "#34495e",
		"Chronic Other": "#95a5a6",
	};

	function nodeCard(node) {
		const conds = (node.conditions || [])
			.map((c) => `<span class="badge mr-1" style="background:${categoryColor[c.condition_category] || "#777"}">${frappe.utils.escape_html(c.condition_category)}</span>`)
			.join("");
		const genderIcon = node.gender === "female" ? "♀" : node.gender === "male" ? "♂" : "•";
		return `<div class="hc-genogram-node d-inline-block m-2 p-3 bg-white border rounded shadow-sm text-center" style="min-width:140px">
			<div style="font-size:1.4rem">${genderIcon}</div>
			<strong>${frappe.utils.escape_html(node.name)}</strong>
			<div class="text-muted small">${frappe.utils.escape_html(node.relationship)}</div>
			<div class="mt-2">${conds || `<span class="text-muted small">${__("No recorded hereditary flags")}</span>`}</div>
		</div>`;
	}

	function renderTree(data) {
		if (!data || !data.nodes) {
			$canvas.html(`<p class="text-muted">${__("No data")}</p>`);
			return;
		}
		const head = data.nodes.filter((n) => n.relationship === "Head");
		const spouse = data.nodes.filter((n) => n.relationship === "Spouse");
		const children = data.nodes.filter((n) => n.relationship === "Child");
		const others = data.nodes.filter((n) => !["Head", "Spouse", "Child"].includes(n.relationship));

		let html = `<h5 class="mb-3">${frappe.utils.escape_html(data.family_name || data.family_unit)}</h5>`;
		if (data.shared_genetic_risk_notes) {
			html += `<p class="alert alert-warning py-2">${frappe.utils.escape_html(data.shared_genetic_risk_notes)}</p>`;
		}
		html += `<div class="text-center mb-3">${head.map(nodeCard).join("")}${spouse.map(nodeCard).join("")}</div>`;
		if (children.length) {
			html += `<div class="text-center border-top pt-3">${children.map(nodeCard).join("")}</div>`;
		}
		if (others.length) {
			html += `<div class="text-center border-top pt-3 mt-3"><em class="text-muted">${__("Other members")}</em><br>${others.map(nodeCard).join("")}</div>`;
		}
		$canvas.html(html);
	}

	function loadTree() {
		const fu = familyUnit.get_value();
		if (!fu) return frappe.msgprint(__("Select a family unit"));
		frappe.call({
			method: "omnexa_healthcare.api.family_unit.get_family_tree",
			args: { family_unit: fu },
			callback(r) { renderTree(r.message); },
		});
	}

	page.set_primary_action(__("Load tree"), loadTree);
	page.add_menu_item(__("Open FM dashboard"), () => {
		const fu = familyUnit.get_value();
		frappe.set_route("healthcare-family-medicine-dashboard");
		if (fu) frappe.route_options = { family_unit: fu };
	});
	page.add_menu_item(__("Add family history"), () => {
		const fu = familyUnit.get_value();
		if (!fu) return frappe.msgprint(__("Select a family unit"));
		frappe.new_doc("Healthcare Family History", { family_unit: fu });
	});
};
