frappe.pages["healthcare-pharmacy-desk"].on_page_load = function (wrapper) {
	const OJ = window.OmnexaJourney;
	if (!OJ || !OJ.mountDeskPage || !OJ.embedRetailPos) {
		frappe.msgprint(__("Run: bench build --app omnexa_healthcare && bench build --app omnexa_core"));
		return;
	}

	const { company, branch } = OJ.resolveCompanyBranch();
	const $mount = OJ.mountDeskPage(wrapper, __("Pharmacy Desk"));
	const state = {
		tab: "pos",
		patient: null,
		warehouse: null,
		data: null,
		pos: null,
		cdsAlerts: [],
		accounts: null,
		purchases: null,
	};

	function flt(v) {
		return parseFloat(v || 0) || 0;
	}
	function money(v) {
		return flt(v).toFixed(2);
	}

	const TAB_NAV_MAP = {
		products: "products",
		customers: "accounts",
		suppliers: "purchases",
		purchases: "purchases",
		inventory: "stock",
		reports: "accounts",
		offers: "pos",
		expenses: "accounts",
		settings: "products",
	};

	function tabBtn(id, label) {
		const cls = state.tab === id ? "oj-btn-primary" : "oj-btn-outline";
		return `<button type="button" class="oj-btn ${cls} oj-tab-btn" data-tab="${id}">${label}</button>`;
	}

	function renderCdsAlerts($target) {
		if (!state.cdsAlerts.length) {
			$target.empty();
			return;
		}
		const rows = state.cdsAlerts
			.map(
				(a) =>
					`<li><span class="oj-status-badge oj-status-unpaid">${OJ.esc(a.severity || "Info")}</span> ${OJ.esc(a.message || a.description || "")}</li>`
			)
			.join("");
		$target.html(
			`<div class="oj-panel" style="border-inline-start:4px solid var(--oj-warning,#f0ad4e);margin:10px 0">
				<strong>${OJ.t("تنبiehات CDS", "CDS Alerts")}</strong>
				<ul style="margin:8px 0 0;padding-inline-start:18px">${rows}</ul>
			</div>`
		);
	}

	async function refreshCdsFromPos($target) {
		if (!state.patient || !state.pos || !state.pos.state || !state.pos.state.invoiceDetail) {
			state.cdsAlerts = [];
			renderCdsAlerts($target);
			return;
		}
		const lines = (state.pos.state.invoiceDetail.items || []).map((row) => ({
			item: row.item_code,
			qty: row.qty,
			rate: row.rate,
		}));
		if (!lines.length) {
			state.cdsAlerts = [];
			renderCdsAlerts($target);
			return;
		}
		try {
			const res = await OJ.call("omnexa_healthcare.api.pharmacy_desk.check_pharmacy_dispense_cds", {
				patient: state.patient,
				lines: JSON.stringify(lines),
			});
			state.cdsAlerts = res.alerts || [];
			renderCdsAlerts($target);
		} catch (e) {
			OJ.showCallError(e);
		}
	}

	async function setPatientBillingCustomer(patient) {
		if (!patient || !state.pos || !state.pos.state || !state.pos.state.invoiceName) return;
		const customer = await frappe.db.get_value("Healthcare Patient", patient, "billing_customer");
		if (!customer || !customer.message || !customer.message.billing_customer) return;
		frappe.call({
			method: `${state.pos.API}.set_retail_pos_customer`,
			args: {
				invoice_name: state.pos.state.invoiceName,
				customer: customer.message.billing_customer,
			},
			callback(r) {
				if (r.message && state.pos) {
					state.pos.state.invoiceDetail = r.message;
					state.pos.state.customer = customer.message.billing_customer;
					if (typeof state.pos.render_cart === "function") state.pos.render_cart();
				}
			},
		});
	}

	async function addItemToRetailPos(itemCode, qty) {
		if (!state.pos) {
			frappe.msgprint(OJ.t("انتظر تحميل نقطة البيع", "Wait for POS to load"));
			return;
		}
		const pos = state.pos;
		if (!pos.state.invoiceName) {
			await new Promise((resolve) => pos.create_invoice(resolve));
		}
		return new Promise((resolve, reject) => {
			frappe.call({
				method: `${pos.API}.add_item_to_retail_pos`,
				args: { invoice_name: pos.state.invoiceName, item_code: itemCode, qty: qty || 1 },
				callback(r) {
					pos.state.invoiceDetail = r.message;
					if (typeof pos.render_cart === "function") pos.render_cart();
					refreshCdsFromPos($(".oj-cds-mount"));
					resolve(r.message);
				},
				error: reject,
			});
		});
	}

	async function loadRx($target, patient) {
		if (!patient) {
			$target.html(`<p class="oj-muted">${OJ.t("ابحث عن مريض", "Search patient")}</p>`);
			return;
		}
		$target.html(OJ.loading());
		const rows = await OJ.call("omnexa_healthcare.api.journey_role_desks.get_patient_prescriptions", {
			patient,
			company,
			warehouse: state.warehouse,
		});
		if (!rows.length) {
			$target.html(`<p class="oj-muted">${OJ.t("لا توجد روشتات", "No prescriptions")}</p>`);
			return;
		}
		const html = rows
			.map((r) => {
				const stock = r.can_dispense
					? `<span class="oj-status-badge oj-status-paid">${OJ.t("متوفر", "In stock")} (${r.on_hand})</span>`
					: `<span class="oj-status-badge oj-status-unpaid">${OJ.t("غير متوفر", "Out of stock")}</span>`;
				const batch = r.batch_no ? ` · ${OJ.t("دفعة", "Batch")} ${OJ.esc(r.batch_no)}` : "";
				return `<div class="oj-clinic-card" style="margin-bottom:10px;text-align:start">
					<strong>${OJ.esc(r.medication_text)}</strong> ${stock}<br>
					<span class="oj-muted">${OJ.esc(r.dosage_text || "")} · ${OJ.esc(r.item_label || "")}${batch}</span><br>
					<button type="button" class="oj-btn oj-btn-sm oj-btn-primary oj-add-rx-pos" data-code="${OJ.esc(r.resolved_item_code || "")}" ${r.can_dispense ? "" : "disabled"}>${OJ.t("لنقطة البيع", "Add to POS")}</button>
					<button type="button" class="oj-btn oj-btn-sm oj-btn-success oj-dispense-now" data-item="${OJ.esc(r.resolved_item || "")}" ${r.can_dispense ? "" : "disabled"}>${OJ.t("صرف فوري", "Dispense now")}</button>
					<button type="button" class="oj-btn oj-btn-sm oj-btn-outline oj-defer-rx" data-rx="${OJ.esc(r.name)}">${OJ.t("تأجيل", "Defer")}</button>
				</div>`;
			})
			.join("");
		$target.empty().html(html);
		$target.find(".oj-add-rx-pos").on("click", async function () {
			const code = $(this).attr("data-code");
			if (!code) return;
			try {
				await addItemToRetailPos(code, 1);
				frappe.show_alert({ message: OJ.t("أُضيف لنقطة البيع", "Added to POS"), indicator: "green" });
			} catch (e) {
				OJ.showCallError(e);
			}
		});
		$target.find(".oj-dispense-now").on("click", async function () {
			const item = $(this).attr("data-item");
			if (!item || !state.patient) return;
			try {
				await OJ.call("omnexa_healthcare.api.pharmacy_desk.pharmacy_pos_checkout", {
					patient: state.patient,
					lines: JSON.stringify([{ item, qty: 1 }]),
					warehouse: state.warehouse,
					company,
					branch,
				});
				frappe.show_alert({ message: OJ.t("تم الصرف", "Dispensed"), indicator: "green" });
				loadRx($target, state.patient);
			} catch (e) {
				OJ.showCallError(e);
			}
		});
		$target.find(".oj-defer-rx").on("click", async function () {
			await OJ.call("omnexa_healthcare.api.pharmacy_desk.defer_prescription", {
				medication_statement: $(this).attr("data-rx"),
			});
			frappe.show_alert({ message: OJ.t("تم التأجيل", "Deferred"), indicator: "blue" });
			loadRx($target, state.patient);
		});
	}

	function renderRxPanel($panel) {
		$panel.html(`
			<div class="oj-panel oj-pharmacy-rx-panel">
				<h4>${OJ.t("صرف الروشتة", "Prescription Dispense")}</h4>
				<p class="oj-muted">${OJ.t("Retail POS من النظام + ربط المريض", "Core Retail POS + patient linkage")}</p>
				${OJ.patientSearchBar({ placeholder: OJ.t("مريض — MRN / اسم / جوال", "Patient search") })}
				<div class="oj-cds-mount"></div>
				<div class="oj-rx-mount" style="margin-top:10px"></div>
			</div>`);
		OJ.bindPatientSearch($panel, (row) => {
			state.patient = row.patient || row.name;
			loadRx($panel.find(".oj-rx-mount"), state.patient);
			setPatientBillingCustomer(state.patient);
			refreshCdsFromPos($panel.find(".oj-cds-mount"));
		}, branch);
		if (state.patient) loadRx($panel.find(".oj-rx-mount"), state.patient);
	}

	async function ensureRetailPos($host) {
		if (state.pos && state.pos.$root) {
			$host.empty().append(state.pos.$root);
			return state.pos;
		}
		const pos = await OJ.embedRetailPos($host[0], {
			onNavigate(nav) {
				const tab = TAB_NAV_MAP[nav] || nav;
				if (tab === "pos") return;
				switchTab(tab);
			},
			onBeforeCompleteSale(posState, proceed) {
				if (!state.patient) {
					proceed();
					return;
				}
				const lines = (posState.invoiceDetail && posState.invoiceDetail.items) || [];
				if (!lines.length) {
					proceed();
					return;
				}
				OJ.call("omnexa_healthcare.api.pharmacy_desk.check_pharmacy_dispense_cds", {
					patient: state.patient,
					lines: JSON.stringify(lines.map((row) => ({ item: row.item_code, qty: row.qty, rate: row.rate }))),
				})
					.then((cds) => {
						const critical = (cds.alerts || []).filter((a) =>
							["contraindicated", "critical"].includes(String(a.severity || "").toLowerCase())
						);
						if (!critical.length) {
							proceed();
							return;
						}
						frappe.confirm(
							OJ.t("تنبيهات CDS حرجة — متابعة البيع؟", "Critical CDS — proceed with sale?"),
							proceed,
							() => {}
						);
					})
					.catch((e) => OJ.showCallError(e));
			},
			onSaleComplete(invoiceName) {
				if (!state.patient || !invoiceName) return;
				OJ.call("omnexa_healthcare.api.pharmacy_desk.link_retail_pos_patient_sale", {
					patient: state.patient,
					sales_invoice: invoiceName,
					warehouse: state.warehouse,
					company,
					branch,
				}).catch((e) => OJ.showCallError(e));
			},
		});
		state.pos = pos || window.omnexa_core.retail_pos;
		if (state.pos && typeof state.pos.render_cart === "function") {
			const origRenderCart = state.pos.render_cart.bind(state.pos);
			state.pos.render_cart = function () {
				origRenderCart();
				refreshCdsFromPos($(".oj-cds-mount"));
			};
		}
		return state.pos;
	}

	async function renderPosTab($body) {
		$body.html(`
			<div class="oj-pharmacy-pos-row">
				<div class="oj-pharmacy-rx-col"></div>
				<div class="oj-retail-pos-host"></div>
			</div>`);
		renderRxPanel($body.find(".oj-pharmacy-rx-col"));
		await ensureRetailPos($body.find(".oj-retail-pos-host"));
	}

	function renderStockTab($body) {
		const d = state.data || {};
		const batchRows = (d.stock_rows || []).flatMap((r) =>
			(r.batches || []).map((b) => ({
				item_name: r.item_name,
				batch_no: b.batch_no,
				expiry_date: b.expiry_date,
				qty_on_hand: b.qty_on_hand,
			}))
		);
		const whOpts = (d.warehouses || [])
			.map((w) => `<option value="${OJ.esc(w.name)}">${OJ.esc(w.warehouse_name || w.name)}</option>`)
			.join("");
		$body.html(`
			<div class="oj-panel">
				<h4>${OJ.t("المخزون والحد الأدنى", "Stock & Par Levels")}</h4>
				<p class="oj-muted">${OJ.t("المخزن", "Warehouse")}: <strong>${OJ.esc(state.warehouse || "—")}</strong></p>
				${OJ.dataTable(
					[
						{ field: "item_name", label: OJ.t("الصنف", "Item") },
						{ field: "on_hand", label: OJ.t("المتوفر", "On Hand") },
						{ field: "par_level", label: OJ.t("الحد الأدنى", "Par") },
						{ field: "reorder_qty", label: OJ.t("إعادة الطلب", "Reorder") },
					],
					d.stock_rows || []
				)}
				<h5 style="margin-top:16px">${OJ.t("دفعات FEFO", "FEFO Batches")}</h5>
				${OJ.dataTable(
					[
						{ field: "item_name", label: OJ.t("الصنف", "Item") },
						{ field: "batch_no", label: OJ.t("الدفعة", "Batch") },
						{ field: "expiry_date", label: OJ.t("الصلاحية", "Expiry") },
						{ field: "qty_on_hand", label: OJ.t("الكمية", "Qty") },
					],
					batchRows
				)}
				<h5 style="margin-top:16px">${OJ.t("تنبيهات النواقص", "Low Stock Alerts")}</h5>
				${OJ.alertList(
					(d.par_alerts || []).map((a) => ({
						level: "warning",
						text: `${a.item} — ${a.on_hand}/${a.par_level} (${OJ.t("نقص", "short")} ${a.shortage})`,
					}))
				)}
				<h5 style="margin-top:16px">${OJ.t("تحويل مخزني", "Stock Transfer")}</h5>
				<div class="oj-filter-bar">
					<div class="oj-filter-item"><label>${OJ.t("من", "From")}</label><select class="oj-tr-src">${whOpts}</select></div>
					<div class="oj-filter-item"><label>${OJ.t("إلى", "To")}</label><select class="oj-tr-tgt">${whOpts}</select></div>
					<div class="oj-filter-item"><label>${OJ.t("الصنف", "Item")}</label><input class="oj-tr-item" placeholder="DEMO-HC-PARA500" /></div>
					<div class="oj-filter-item"><label>${OJ.t("الكمية", "Qty")}</label><input type="number" class="oj-tr-qty" value="10" /></div>
					<button type="button" class="oj-btn oj-btn-primary oj-tr-submit">${OJ.t("تحويل", "Transfer")}</button>
				</div>
			</div>`);
		$body.find(".oj-tr-submit").on("click", async () => {
			const itemCode = ($body.find(".oj-tr-item").val() || "").trim();
			const item = await frappe.db.get_value("Item", { item_code: itemCode, company }, "name");
			if (!item || !item.message || !item.message.name) {
				return frappe.msgprint(OJ.t("صنف غير موجود", "Item not found"));
			}
			try {
				const res = await OJ.call("omnexa_healthcare.api.pharmacy_desk.create_pharmacy_stock_transfer", {
					source_warehouse: $body.find(".oj-tr-src").val(),
					target_warehouse: $body.find(".oj-tr-tgt").val(),
					items: JSON.stringify([{ item: item.message.name, qty: flt($body.find(".oj-tr-qty").val()) }]),
					company,
					branch,
				});
				frappe.show_alert({ message: OJ.t("تم التحويل", "Transferred") + ": " + res.stock_entry, indicator: "green" });
				reloadDashboard().then(() => renderTabBody($(".oj-pharmacy-tab-body")));
			} catch (e) {
				OJ.showCallError(e);
			}
		});
	}

	async function renderPurchaseTab($body) {
		state.purchases = await OJ.call("omnexa_healthcare.api.pharmacy_desk.get_pharmacy_purchases_summary", { company, branch });
		const d = state.data || {};
		const whOpts = (d.warehouses || [])
			.map((w) => `<option value="${OJ.esc(w.name)}" ${w.name === state.warehouse ? "selected" : ""}>${OJ.esc(w.warehouse_name || w.name)}</option>`)
			.join("");
		const p = state.purchases || {};
		$body.html(`
			<div class="oj-panel">
				<h4>${OJ.t("استلام مخزون / مشتريات", "Goods Receipt / Purchases")}</h4>
				<div class="oj-filter-bar">
					<div class="oj-filter-item"><label>${OJ.t("المخزن", "Warehouse")}</label><select class="oj-purchase-wh">${whOpts}</select></div>
					<div class="oj-filter-item"><label>${OJ.t("الصنف", "Item")}</label><input class="oj-purchase-item" placeholder="${OJ.t("كود الصنف", "Item code")}" /></div>
					<div class="oj-filter-item"><label>${OJ.t("الكمية", "Qty")}</label><input type="number" class="oj-purchase-qty" value="50" /></div>
					<div class="oj-filter-item"><label>${OJ.t("السعر", "Rate")}</label><input type="number" class="oj-purchase-rate" value="10" /></div>
					<div class="oj-filter-item"><label>${OJ.t("الدفعة", "Batch")}</label><input class="oj-purchase-batch" placeholder="BATCH-001" /></div>
					<button type="button" class="oj-btn oj-btn-primary oj-purchase-submit">${OJ.t("استلام", "Receive")}</button>
				</div>
				<h5 style="margin-top:16px">${OJ.t("آخر أوامر الشراء", "Recent Purchase Orders")}</h5>
				${OJ.dataTable(
					[
						{ field: "name", label: OJ.t("المرجع", "Ref") },
						{ field: "supplier", label: OJ.t("المورد", "Supplier") },
						{ field: "transaction_date", label: OJ.t("التاريخ", "Date") },
						{ field: "grand_total", label: OJ.t("الإجمالي", "Total") },
						{ field: "status", label: OJ.t("الحالة", "Status") },
					],
					p.purchase_orders || []
				)}
				<h5 style="margin-top:16px">${OJ.t("آخر استلامات", "Recent Receipts")}</h5>
				${OJ.dataTable(
					[
						{ field: "name", label: OJ.t("المرجع", "Ref") },
						{ field: "posting_date", label: OJ.t("التاريخ", "Date") },
						{ field: "total_amount", label: OJ.t("القيمة", "Amount") },
						{ field: "remarks", label: OJ.t("ملاحظات", "Remarks") },
					],
					p.material_receipts || []
				)}
			</div>`);
		$body.find(".oj-purchase-submit").on("click", async () => {
			const itemCode = ($body.find(".oj-purchase-item").val() || "").trim();
			const item = await frappe.db.get_value("Item", { item_code: itemCode, company }, "name");
			if (!item || !item.message || !item.message.name) {
				return frappe.msgprint(OJ.t("صنف غير موجود", "Item not found"));
			}
			try {
				const res = await OJ.call("omnexa_healthcare.api.pharmacy_desk.create_pharmacy_purchase_receipt", {
					warehouse: $body.find(".oj-purchase-wh").val(),
					items: JSON.stringify([
						{
							item: item.message.name,
							qty: flt($body.find(".oj-purchase-qty").val()),
							rate: flt($body.find(".oj-purchase-rate").val()),
							batch_no: ($body.find(".oj-purchase-batch").val() || "").trim() || undefined,
						},
					]),
					company,
					branch,
				});
				frappe.show_alert({ message: OJ.t("تم الاستلام", "Received") + ": " + res.stock_entry, indicator: "green" });
				renderPurchaseTab($body);
			} catch (e) {
				OJ.showCallError(e);
			}
		});
	}

	async function renderAccountsTab($body) {
		state.accounts = await OJ.call("omnexa_healthcare.api.pharmacy_desk.get_pharmacy_accounts_summary", { company, branch });
		const a = state.accounts || {};
		$body.html(`
			<div class="oj-panel">
				<h4>${OJ.t("الحسابات — مبيعات وتحصيل", "Accounts — Sales & Collections")}</h4>
				<p class="oj-muted">${OJ.t("إيراد اليوم", "Revenue today")}: <strong>${money(a.revenue_today)}</strong> · ${OJ.t("تحصيل اليوم", "Collections today")}: <strong>${money(a.collections_today)}</strong></p>
				<h5>${OJ.t("فواتير المبيعات", "Sales Invoices")}</h5>
				${OJ.dataTable(
					[
						{ field: "name", label: OJ.t("الفاتورة", "Invoice") },
						{ field: "customer", label: OJ.t("العميل", "Customer") },
						{ field: "posting_date", label: OJ.t("التاريخ", "Date") },
						{ field: "grand_total", label: OJ.t("الإجمالي", "Total") },
						{ field: "status", label: OJ.t("الحالة", "Status") },
					],
					a.sales_invoices || []
				)}
				<h5 style="margin-top:16px">${OJ.t("سندات القبض", "Payment Entries")}</h5>
				${OJ.dataTable(
					[
						{ field: "name", label: OJ.t("السند", "Entry") },
						{ field: "party", label: OJ.t("الطرف", "Party") },
						{ field: "posting_date", label: OJ.t("التاريخ", "Date") },
						{ field: "paid_amount", label: OJ.t("المبلغ", "Amount") },
						{ field: "mode_of_payment", label: OJ.t("طريقة الدفع", "Method") },
					],
					a.payment_entries || []
				)}
				<h5 style="margin-top:16px">${OJ.t("حركات المخزون المحاسبية", "Stock Entries")}</h5>
				${OJ.dataTable(
					[
						{ field: "name", label: OJ.t("المرجع", "Ref") },
						{ field: "posting_date", label: OJ.t("التاريخ", "Date") },
						{ field: "purpose", label: OJ.t("الغرض", "Purpose") },
						{ field: "total_amount", label: OJ.t("القيمة", "Amount") },
					],
					a.stock_entries || []
				)}
			</div>`);
	}

	async function renderProductsTab($body) {
		$body.html(`
			<div class="oj-panel">
				<h4>${OJ.t("الأصناف — بحث وإضافة للـ POS", "Products — search & add to POS")}</h4>
				<div class="oj-filter-bar">
					<input type="text" class="oj-prod-query" placeholder="${OJ.t("اسم الدواء أو الكود", "Drug name or code")}" />
					<button type="button" class="oj-btn oj-btn-outline oj-prod-search">${OJ.t("بحث", "Search")}</button>
				</div>
				<div class="oj-prod-results"></div>
			</div>`);
		const runSearch = async () => {
			const q = ($body.find(".oj-prod-query").val() || "").trim();
			const items = await OJ.call("omnexa_healthcare.api.pharmacy_desk.search_pharmacy_pos_items", {
				query: q,
				company,
				warehouse: state.warehouse,
			});
			const $r = $body.find(".oj-prod-results").empty();
			if (!items.length) {
				$r.html(`<p class="oj-muted">${OJ.t("لا نتائج", "No results")}</p>`);
				return;
			}
			const rows = items
				.map(
					(it) => `<tr>
					<td>${OJ.esc(it.item_name)}</td>
					<td>${OJ.esc(it.item_code)}</td>
					<td>${it.on_hand}</td>
					<td>${money(it.rate)}</td>
					<td><button type="button" class="oj-btn oj-btn-sm oj-btn-primary oj-prod-add" data-code="${OJ.esc(it.item_code)}">${OJ.t("للـ POS", "To POS")}</button></td>
				</tr>`
				)
				.join("");
			$r.html(`<table class="oj-data-table"><thead><tr>
				<th>${OJ.t("الصنف", "Item")}</th><th>${OJ.t("الكود", "Code")}</th>
				<th>${OJ.t("المتوفر", "On Hand")}</th><th>${OJ.t("السعر", "Rate")}</th><th></th>
			</tr></thead><tbody>${rows}</tbody></table>`);
			$r.find(".oj-prod-add").on("click", async function () {
				try {
					await addItemToRetailPos($(this).attr("data-code"), 1);
					switchTab("pos");
					frappe.show_alert({ message: OJ.t("أُضيف للسلة", "Added to cart"), indicator: "green" });
				} catch (e) {
					OJ.showCallError(e);
				}
			});
		};
		$body.find(".oj-prod-search").on("click", runSearch);
		$body.find(".oj-prod-query").on("keydown", (e) => {
			if (e.key === "Enter") runSearch();
		});
		runSearch();
	}

	function renderTabBody($tabBody) {
		if (state.tab === "pos") {
			renderPosTab($tabBody).catch((e) => OJ.showCallError(e));
			return;
		}
		if (state.pos && window.omnexa_core && omnexa_core.retail_product_manager) {
			omnexa_core.retail_product_manager.close();
		}
		if (state.tab === "stock") {
			renderStockTab($tabBody);
		} else if (state.tab === "purchase") {
			renderPurchaseTab($tabBody).catch((e) => OJ.showCallError(e));
		} else if (state.tab === "accounts") {
			renderAccountsTab($tabBody).catch((e) => OJ.showCallError(e));
		} else if (state.tab === "products") {
			renderProductsTab($tabBody).catch((e) => OJ.showCallError(e));
		}
	}

	function switchTab(tab) {
		state.tab = tab;
		const $tabs = $(".oj-pharmacy-tabs");
		$tabs.find(".oj-tab-btn").removeClass("oj-btn-primary").addClass("oj-btn-outline");
		$tabs.find(`.oj-tab-btn[data-tab="${tab}"]`).removeClass("oj-btn-outline").addClass("oj-btn-primary");
		renderTabBody($(".oj-pharmacy-tab-body"));
	}

	async function reloadDashboard() {
		state.data = await OJ.call("omnexa_healthcare.api.journey_role_desks.get_pharmacy_dashboard", { company, branch });
		state.warehouse = state.warehouse || state.data.warehouse;
		return state.data;
	}

	async function render() {
		const data = await reloadDashboard();
		const kpiCards = [
			{ value: data.orders_pending, label: OJ.t("روشتات", "Rx") },
			{ value: data.dispensed_today, label: OJ.t("صرف اليوم", "Dispensed") },
			{ value: data.low_stock_items, label: OJ.t("نواقص", "Low Stock") },
		];
		const $body = $(`<div class="oj-pharmacy-layout"></div>`);
		const $tabs = $(`<div class="oj-filter-bar oj-pharmacy-tabs"></div>`).appendTo($body);
		$tabs.append(tabBtn("pos", OJ.t("نقطة البيع", "Point of Sale")));
		$tabs.append(tabBtn("products", OJ.t("الأصناف", "Products")));
		$tabs.append(tabBtn("purchase", OJ.t("المشتريات", "Purchases")));
		$tabs.append(tabBtn("stock", OJ.t("المخzون", "Inventory")));
		$tabs.append(tabBtn("accounts", OJ.t("الحسابات", "Accounts")));
		const $tabBody = $(`<div class="oj-pharmacy-tab-body"></div>`).appendTo($body);
		$tabs.find(".oj-tab-btn").on("click", function () {
			switchTab($(this).attr("data-tab"));
		});
		const $shell = OJ.shell({
			title: OJ.t("الصيدلية — ERP متكامل", "Pharmacy — Integrated ERP"),
			subtitle: OJ.t("Retail POS · مخزون · مشtريات · حسابات", "Retail POS · Stock · Purchases · Accounts"),
			role: OJ.t("صيدلي/ة", "Pharmacist"),
			kpis: kpiCards,
			sidebar: OJ.defaultSidebar("pharmacy"),
			bodyEl: $body,
			homeRoute: "/app/healthcare-pharmacy-desk",
		});
		$mount.empty().append($shell);
		renderTabBody($tabBody);
	}

	render().catch((e) => OJ.showCallError(e));
};
