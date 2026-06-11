frappe.pages["healthcare-telehealth-room"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Telehealth Video Room"),
		single_column: true,
	});
	const $body = $(page.body);
	const $toolbar = $(`<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"></div>`).appendTo($body);
	const session = frappe.ui.form.make_control({
		parent: $toolbar,
		df: { fieldtype: "Link", options: "Healthcare Telehealth Session", label: __("Session"), fieldname: "session" },
		render_input: true,
	});
	session.$wrapper.css({ minWidth: "280px" });
	session.refresh();
	const $frame = $(`<div id="telehealth-frame" style="min-height:480px;border:1px solid var(--border-color);border-radius:8px"></div>`).appendTo($body);
	page.set_primary_action(__("Join waiting room"), () => join_room("patient"));
	page.set_secondary_action(__("Start session"), () => {
		const s = session.get_value();
		if (!s) return frappe.msgprint(__("Select a session."));
		frappe.call({
			method: "omnexa_healthcare.api.telehealth.start_telehealth_session",
			args: { session: s },
			callback() {
				join_room("provider");
			},
		});
	});
	function join_room(role) {
		const s = session.get_value();
		if (!s) return frappe.msgprint(__("Select a session."));
		frappe.call({
			method: "omnexa_healthcare.api.telehealth.join_virtual_waiting_room",
			args: { session: s, role },
			freeze: true,
			callback(r) {
				const msg = r.message || {};
				if (msg.join_url) {
					$frame.html(
						`<iframe src="${frappe.utils.escape_html(msg.join_url)}" allow="camera; microphone; fullscreen" style="width:100%;height:520px;border:0"></iframe>`
					);
				}
			},
		});
	}
};
