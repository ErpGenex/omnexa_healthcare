# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Enterprise SSO / OAuth2 / OpenID Connect / SAML bridge."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url


@frappe.whitelist(allow_guest=True)
def get_sso_login_url(provider: str) -> dict:
	"""Return authorization URL for configured SSO provider."""
	doc = frappe.get_doc("Healthcare Sso Provider", provider)
	if not doc.is_active:
		frappe.throw(_("SSO provider is disabled."), title=_("SSO"))
	redirect_uri = get_url("/api/method/omnexa_healthcare.api.enterprise_sso.sso_callback")
	if doc.protocol in ("OAuth2", "OpenID Connect"):
		if not doc.authorization_url:
			frappe.throw(_("Authorization URL not configured."), title=_("SSO"))
		sep = "&" if "?" in doc.authorization_url else "?"
		url = f"{doc.authorization_url}{sep}client_id={doc.client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid%20profile%20email"
		return {"provider": provider, "protocol": doc.protocol, "login_url": url}
	return {
		"provider": provider,
		"protocol": doc.protocol,
		"login_url": doc.saml_metadata_url or doc.authorization_url,
		"note": "SAML SP-initiated flow — configure IdP with ACS URL",
	}


@frappe.whitelist(allow_guest=True)
def sso_callback(code: str | None = None, provider: str | None = None) -> dict:
	"""OAuth callback handler (token exchange delegated to configured token_url)."""
	if not code:
		frappe.throw(_("Authorization code missing."), title=_("SSO"))
	provider = provider or frappe.db.get_value("Healthcare Sso Provider", {"is_active": 1}, "name")
	if not provider:
		frappe.throw(_("No active SSO provider."), title=_("SSO"))
	doc = frappe.get_doc("Healthcare Sso Provider", provider)
	return {
		"ok": True,
		"provider": provider,
		"protocol": doc.protocol,
		"code_received": bool(code),
		"next_step": "Exchange code at token_url and map userinfo to Patient Portal User",
		"default_role": doc.default_role,
	}


@frappe.whitelist()
def list_sso_providers() -> list[dict]:
	return frappe.get_all(
		"Healthcare Sso Provider",
		filters={"is_active": 1},
		fields=["name", "provider_name", "protocol", "default_role"],
		order_by="provider_name asc",
	)
