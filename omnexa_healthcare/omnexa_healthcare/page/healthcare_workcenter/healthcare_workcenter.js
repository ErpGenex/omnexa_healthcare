frappe.pages["healthcare-workcenter"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage) {
		frappe.ui.make_app_page({ parent: wrapper, title: __("Healthcare Workcenter"), single_column: true });
		return;
	}
	const $mount = OJ.mountDeskPage(wrapper, __("Healthcare Workcenter"));
	let activePhaseId = "";

	function phaseLabel(phase) {
		return OJ.lang() === "ar" ? phase.label_ar : phase.label_en;
	}

	function phaseSummary(phase) {
		return OJ.lang() === "ar" ? phase.summary_ar : phase.summary_en;
	}

	function renderPhasePanels(phases) {
		const $row = $('<div class="oj-phase-dashboard"></div>');
		(phases || []).forEach((phase) => {
			const stats = phase.stats || {};
			const activeCls = phase.active ? " oj-phase-card-active" : "";
			const readyBadge = phase.ready
				? `<span class="oj-phase-badge oj-phase-badge-ready">${OJ.t("جاهز", "Ready")}</span>`
				: `<span class="oj-phase-badge">${OJ.t("غير مُفعّل", "Not provisioned")}</span>`;
			const networkHtml =
				phase.id === "national" && phase.network
					? `<div class="oj-phase-network">
						<strong>${OJ.t("الشبكة", "Network")}:</strong>
						${phase.network.governorate_count} ${OJ.t("محافظة", "gov.")} ·
						${phase.network.branch_count} ${OJ.t("فرع", "branches")} ·
						${phase.network.seeded_branch_count} ${OJ.t("مزروع", "seeded")}
					</div>`
					: "";
			const $card = $(`
				<div class="oj-phase-card${activeCls}" data-phase="${OJ.esc(phase.id)}">
					<div class="oj-phase-card-head">
						<span class="oj-phase-icon">${phase.icon || "🏥"}</span>
						<div>
							<h4>${OJ.esc(phaseLabel(phase))}</h4>
							<p class="oj-muted">${OJ.esc(phaseSummary(phase))}</p>
						</div>
						${readyBadge}
					</div>
					<div class="oj-phase-meta">
						<div><strong>${OJ.t("الشركة", "Company")}:</strong> <code>${OJ.esc(phase.company || "—")}</code></div>
						<div><strong>${OJ.t("الفرع", "Branch")}:</strong> <code>${OJ.esc(phase.branch || "—")}</code></div>
						<div><strong>${OJ.t("البوابات", "Portals")}:</strong> ${phase.portal_count || 0}</div>
					</div>
					<div class="oj-phase-stats">
						<div class="oj-phase-stat"><span>${stats.patients || 0}</span><small>${OJ.t("مرضى", "Patients")}</small></div>
						<div class="oj-phase-stat"><span>${stats.departments || 0}</span><small>${OJ.t("أقسام", "Depts")}</small></div>
						<div class="oj-phase-stat"><span>${stats.beds || 0}</span><small>${OJ.t("أسرة", "Beds")}</small></div>
					</div>
					${networkHtml}
					<div class="oj-phase-actions">
						<button type="button" class="oj-btn oj-btn-primary oj-phase-activate" data-phase="${OJ.esc(phase.id)}">
							${OJ.t("تفعيل وزرع", "Activate & Seed")}
						</button>
						<button type="button" class="oj-btn oj-btn-outline oj-phase-switch" data-phase="${OJ.esc(phase.id)}" ${phase.ready ? "" : "disabled"}>
							${OJ.t("التبديل", "Switch")}
						</button>
						${phase.site_url ? `<a class="oj-btn oj-btn-outline oj-phase-link" href="${OJ.esc(phase.site_url)}" target="_blank">${OJ.t("الموقع", "Website")}</a>` : ""}
						${phase.booking_url ? `<a class="oj-btn oj-btn-outline oj-phase-link" href="${OJ.esc(phase.booking_url)}" target="_blank">${OJ.t("الحجز", "Booking")}</a>` : ""}
					</div>
				</div>
			`);
			$row.append($card);
		});
		return $row;
	}

	function renderNationalTree(network) {
		if (!network || !(network.governorates || []).length) return "";
		const $wrap = $('<div class="oj-panel oj-national-tree" style="margin-top:16px"></div>');
		$wrap.append(`<h4>${OJ.t("شبكة المحافظات والفروع", "Governorates & Branches Network")}</h4>`);
		(network.governorates || []).forEach((gov) => {
			const $gov = $(`<div class="oj-gov-block"></div>`);
			const govTitle = OJ.lang() === "ar" ? gov.label_ar : gov.label_en;
			$gov.append(
				`<h5 class="oj-gov-title">${OJ.esc(govTitle)} <code>${OJ.esc(gov.company)}</code></h5>`
			);
			const rows = (gov.branches || []).map((b) => ({
				branch: b.branch,
				name: b.name_ar,
				facility: b.facility,
				status: b.seeded ? OJ.t("مزروع", "Seeded") : b.exists ? OJ.t("فرع فقط", "Branch only") : OJ.t("غير موجود", "Missing"),
				site: b.site_slug || "—",
			}));
			$gov.append(
				OJ.dataTable(
					[
						{ field: "branch", label: OJ.t("الفرع", "Branch") },
						{ field: "name", label: OJ.t("الاسم", "Name") },
						{ field: "facility", label: OJ.t("النوع", "Type") },
						{ field: "status", label: OJ.t("الحالة", "Status") },
						{ field: "site", label: OJ.t("رابط", "Link") },
					],
					rows
				)
			);
			$wrap.append($gov);
		});
		return $wrap;
	}

	function filterPortalGroups(groups, phases) {
		const active = (phases || []).find((p) => p.id === activePhaseId);
		if (!active || !active.portal_ids) return groups;
		const allowed = new Set(active.portal_ids);
		return (groups || [])
			.map((g) => ({
				...g,
				portals: (g.portals || []).filter((p) => allowed.has(p.id)),
			}))
			.filter((g) => (g.portals || []).length);
	}

	function bindPhaseActions($body) {
		$body.find(".oj-phase-activate").on("click", function () {
			const phaseId = $(this).data("phase");
			frappe.confirm(
				OJ.t("سيتم إنشاء/تحديث بيانات هذه المرحلة. هل تريد المتابعة؟", "This will provision/update demo data for the phase. Continue?"),
				() => {
					frappe.call({
						method: "omnexa_healthcare.api.deployment_phase_hub.activate_deployment_phase",
						args: { phase_id: phaseId, force: 1 },
						freeze: true,
						callback(r) {
							frappe.show_alert({
								message: OJ.t("تم تفعيل المرحلة", "Phase activated"),
								indicator: "green",
							});
							if (r.message && r.message.message) frappe.msgprint(r.message.message);
							render();
						},
					});
				}
			);
		});
		$body.find(".oj-phase-switch").on("click", function () {
			const phaseId = $(this).data("phase");
			frappe.call({
				method: "omnexa_healthcare.api.deployment_phase_hub.set_deployment_phase_context",
				args: { phase_id: phaseId },
				freeze: true,
				callback() {
					frappe.show_alert({ message: OJ.t("تم التبديل", "Context switched"), indicator: "green" });
					render();
				},
			});
		});
	}

	async function render() {
		const [creds, groups, phaseDash] = await Promise.all([
			OJ.call("omnexa_healthcare.api.healthcare_role_demo.get_healthcare_demo_credentials"),
			OJ.call("omnexa_healthcare.api.portal_catalog.get_grouped_portal_catalog"),
			OJ.call("omnexa_healthcare.api.deployment_phase_hub.get_deployment_phases_dashboard"),
		]);
		activePhaseId = phaseDash.active_phase || "";
		const phases = phaseDash.phases || [];
		const nationalPhase = phases.find((p) => p.id === "national");

		const $body = $("<div class='oj-demo-hub'></div>");
		$body.append(`<div class="oj-panel oj-phase-panel-intro">
			<h4>${OJ.t("لوحات التشغيل على مراحل", "Deployment Phase Control Panels")}</h4>
			<p class="oj-muted">${OJ.t(
				"اختر سينario: عيادة خاصة · مستشفى كامل · شبكة وطنية بالمحافظات. التفعيل يزرع البيانات ويضبط Company/Branch.",
				"Pick a scenario: private clinic · full hospital · national network. Activation seeds data and sets Company/Branch."
			)}</p>
			${activePhaseId ? `<p><strong>${OJ.t("المرحلة النشطة", "Active phase")}:</strong> <code>${OJ.esc(activePhaseId)}</code> · ${OJ.t("الشركة", "Company")}: <code>${OJ.esc(phaseDash.default_company || "")}</code> · ${OJ.t("الفرع", "Branch")}: <code>${OJ.esc(phaseDash.default_branch || "")}</code></p>` : ""}
		</div>`);
		$body.append(renderPhasePanels(phases));
		if (nationalPhase && nationalPhase.network) {
			$body.append(renderNationalTree(nationalPhase.network));
		}

		$body.append(`<div class="oj-panel" style="margin-top:16px"><h4>${OJ.t("حسابات الديمو", "Demo Accounts")}</h4>
			<p class="oj-muted">${OJ.t("كلمة المرور", "Password")}: <code>${OJ.esc(creds.password)}</code></p>
			<div class="oj-filter-bar">
				<button type="button" class="oj-btn oj-btn-outline oj-sync-perms">${OJ.t("مزامنة الصلاحيات", "Sync Permissions")}</button>
				<button type="button" class="oj-btn oj-btn-outline oj-seed-devices">${OJ.t("أجهزة تجريبية", "Seed Demo Devices")}</button>
			</div>
			${OJ.dataTable(
				[
					{ field: "role", label: OJ.t("الدور", "Role") },
					{ field: "email", label: OJ.t("البريد", "Email") },
					{ field: "name", label: OJ.t("الاسم", "Name") },
					{ field: "route", label: OJ.t("البوابة", "Portal") },
				],
				(creds.users || []).map((u) => ({ ...u, route: u.route }))
			)}
		</div>`);

		const filteredGroups = activePhaseId ? filterPortalGroups(groups, phases) : groups;
		const portalTitle = activePhaseId
			? OJ.t("بوابات المرحلة النشطة", "Active Phase Portals")
			: OJ.t("جميع البوابات", "All Portals");
		$body.append(`<div class="oj-panel oj-demo-portals-panel" style="margin-top:16px"><h4>${portalTitle}</h4></div>`);
		const $portalMount = $body.find(".oj-demo-portals-panel");
		(filteredGroups || groups || []).forEach((g) => {
			const title = OJ.lang() === "ar" ? g.label_ar : g.label_en;
			$portalMount.append(`<h4 class="oj-portal-cat-title" style="margin-top:20px">${OJ.esc(title)}</h4>`);
			const clinics = (g.portals || []).map((p) => ({
				id: p.id,
				name: OJ.lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: OJ.t("بوابة خارجية", "Outpatient portal"),
				icon: p.icon || "🏥",
				doctor_count: 1,
				waiting_count: 0,
				route: p.route,
				exists: p.exists,
			}));
			$portalMount.append(
				OJ.clinicGrid(
					clinics.filter((c) => c.exists !== false && c.route),
					(c) => OJ.navigateRoute(c.route)
				)
			);
		});

		bindPhaseActions($body);
		$body.find(".oj-sync-perms").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.utils.healthcare_demo_permissions.sync_healthcare_demo_permissions",
				freeze: true,
				callback() {
					frappe.show_alert({ message: __("Permissions synced"), indicator: "green" });
				},
			});
		});
		$body.find(".oj-seed-devices").on("click", () => {
			frappe.call({
				method: "omnexa_healthcare.api.device_integration.seed_demo_medical_devices",
				freeze: true,
				callback() {
					frappe.show_alert({ message: __("Devices seeded"), indicator: "green" });
				},
			});
		});

		const $shell = OJ.shell({
			title: OJ.t("مركز عمل Omnexa Healthcare", "Omnexa Healthcare Workcenter"),
			subtitle: OJ.t("مراحل التشغيل · البوابات · الأدوار", "Deployment phases · portals · roles"),
			role: OJ.t("مدير النظام", "System Manager"),
			sidebar: OJ.defaultSidebar("admin"),
			bodyEl: $body,
			homeRoute: "/app/healthcare-workcenter",
		});
		$mount.empty().append($shell);
	}

	render().catch((e) => OJ.showCallError(e));
};
