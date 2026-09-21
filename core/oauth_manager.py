# -*- coding: utf-8 -*-
"""
AI Automation Hub - OAuth 2.0 Engine
Handles OAuth authorization flows, token exchanges, user profiles,
and token refresh lifecycles for Google, GitHub, Microsoft, Meta, and Slack.
"""

import json
import urllib.parse
import urllib.request
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from core.execution_logger import (
    get_oauth_app_config,
    create_oauth_state,
    verify_and_consume_oauth_state,
    save_user_integration,
    get_client_by_id
)

OAUTH_PROVIDERS = {
    "google": {
        "name": "Google Workspace / Gmail",
        "icon": "🔴",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "default_scopes": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/drive.file email profile",
        "description": "Gmail emailkezelés, Google Naptár, Google Drive és Dokumentumok 100%-os automatizációja."
    },
    "github": {
        "name": "GitHub",
        "icon": "🐙",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "default_scopes": "repo,workflow,read:user,user:email",
        "description": "Céges repository-k elérése, automatikus hibajegyek, kódellenőrzés és release jegyzékek."
    },
    "microsoft": {
        "name": "Microsoft 365 / Azure AD",
        "icon": "🔵",
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "default_scopes": "offline_access Mail.ReadWrite Calendars.ReadWrite User.Read",
        "description": "Outlook levelezés, Teams értesítések és Microsoft naptárszinkronizáció."
    },
    "meta": {
        "name": "Meta / WhatsApp Business Cloud",
        "icon": "🟢",
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email",
        "default_scopes": "whatsapp_business_messaging,whatsapp_business_management,pages_manage_posts",
        "description": "Hivatalos WhatsApp Business üzenetküldés, Facebook & Instagram lead menedzsment."
    },
    "slack": {
        "name": "Slack",
        "icon": "🟣",
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "userinfo_url": "https://slack.com/api/users.identity",
        "default_scopes": "channels:read,chat:write,commands,incoming-webhook",
        "description": "Csoportos belső csatorna értesítések, vezetői jóváhagyási gombok és Slack botok."
    }
}

def get_provider_details(provider: str) -> Optional[Dict[str, Any]]:
    return OAUTH_PROVIDERS.get(provider.lower())

def build_authorization_url(provider: str, user_id: int, base_url: str) -> Dict[str, Any]:
    prov = provider.lower()
    spec = get_provider_details(prov)
    if not spec:
        raise ValueError(f"Ismeretlen OAuth szolgáltató: '{provider}'")

    config = get_oauth_app_config(prov)
    redirect_uri = f"{base_url.rstrip('/')}/api/v1/oauth/{prov}/callback"
    state = create_oauth_state(user_id=user_id, provider=prov, redirect_uri=redirect_uri)

    client_id = config.get("client_id", "") if config else ""
    sandbox_mode = config.get("sandbox_mode", True) if config else True
    scopes = (config.get("scopes") or spec["default_scopes"]) if config else spec["default_scopes"]

    # Ha a szuper admin még nem konfigurált éles Client ID-t vagy sandbox mód van érvényben,
    # akkor azonnali tesztelhető sandbox callback URL-t adunk vissza!
    if sandbox_mode or not client_id:
        sandbox_code = f"mock_code_{prov}_{secrets.token_hex(8)}"
        auth_url = f"{redirect_uri}?code={sandbox_code}&state={state}&sandbox=1"
        return {
            "auth_url": auth_url,
            "provider": prov,
            "is_sandbox": True,
            "state": state,
            "message": "Sandbox mód aktív (azonnali bemutató és tesztelési lehetőség)."
        }

    # Valós OAuth 2.0 Authorization URL felépítése
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "access_type": "offline", # Google refresh token kérés
        "prompt": "consent"
    }

    if prov == "github":
        params.pop("access_type", None)
        params.pop("prompt", None)

    auth_url = f"{spec['auth_url']}?{urllib.parse.urlencode(params)}"
    return {
        "auth_url": auth_url,
        "provider": prov,
        "is_sandbox": False,
        "state": state,
        "message": "Átirányítás a hivatalos szolgáltatói jóváhagyó képernyőre."
    }

def exchange_code_for_tokens(provider: str, code: str, redirect_uri: str, user_id: int) -> Dict[str, Any]:
    prov = provider.lower()
    spec = get_provider_details(prov)
    if not spec:
        raise ValueError(f"Ismeretlen OAuth szolgáltató: '{provider}'")

    config = get_oauth_app_config(prov)
    sandbox_mode = config.get("sandbox_mode", True) if config else True
    client_id = config.get("client_id", "") if config else ""
    client_secret = config.get("client_secret", "") if config else ""

    user = get_client_by_id(user_id) or {}
    user_email = user.get("email", "ugyfel@cegnev.hu")
    user_name = user.get("full_name", "Megbízó")

    # 1. Sandbox Mock Token csere
    if code.startswith("mock_code_") or sandbox_mode or not (client_id and client_secret):
        now = datetime.now()
        expires_at = (now + timedelta(hours=1)).isoformat()
        
        token_prefix = {
            "google": "ya29.sandbox_google_token_",
            "github": "gho_sandbox_github_token_",
            "microsoft": "EwB_sandbox_ms_token_",
            "meta": "EAAB_sandbox_meta_token_",
            "slack": "xoxb_sandbox_slack_token_"
        }.get(prov, "sandbox_token_")

        creds = {
            "auth_type": "oauth2",
            "provider": prov,
            "is_sandbox": True,
            "access_token": f"{token_prefix}{secrets.token_hex(16)}",
            "refresh_token": f"1//sandbox_refresh_{secrets.token_hex(20)}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": expires_at,
            "scopes": spec["default_scopes"],
            "account_email": user_email,
            "account_name": f"{user_name} ({spec['name']})",
            "connected_at": now.isoformat()
        }

        # Mentés a Vaultba
        integration_id = save_user_integration(
            user_id=user_id,
            service_type=prov,
            service_name=f"{spec['name']} ({user_email})",
            credentials=creds,
            status="connected",
            notes=f"OAuth 2.0 csatlakoztatva: {now.strftime('%Y-%m-%d %H:%M')}"
        )

        return {
            "status": "success",
            "integration_id": integration_id,
            "provider": prov,
            "account_email": user_email,
            "credentials": creds,
            "message": f"'{spec['name']}' sikeresen összekapcsolva OAuth 2.0-val!"
        }

    # 2. Valós OAuth 2.0 Token Endpoint hívás
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = urllib.parse.urlencode(token_payload).encode("utf-8")
    req = urllib.request.Request(spec["token_url"], data=data, headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        resp_data = resp.read().decode("utf-8")
        try:
            token_json = json.loads(resp_data)
        except Exception:
            token_json = dict(urllib.parse.parse_qsl(resp_data))

    access_token = token_json.get("access_token")
    if not access_token:
        err_msg = token_json.get("error_description") or token_json.get("error") or "Nem sikerült access token-t szerezni."
        raise ValueError(f"OAuth hiba ({prov}): {err_msg}")

    refresh_token = token_json.get("refresh_token", "")
    expires_in = int(token_json.get("expires_in", 3600))
    now = datetime.now()
    expires_at = (now + timedelta(seconds=expires_in)).isoformat()

    # Felhasználói profil adatainak lekérése
    account_email = user_email
    account_name = spec["name"]

    try:
        profile_req = urllib.request.Request(
            spec["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}", "User-Agent": "AI-Automation-Hub/2.0"}
        )
        with urllib.request.urlopen(profile_req, timeout=10) as profile_resp:
            profile_data = json.loads(profile_resp.read().decode("utf-8"))
            if prov == "google":
                account_email = profile_data.get("email", user_email)
                account_name = profile_data.get("name", user_name)
            elif prov == "github":
                account_name = profile_data.get("login", user_name)
                account_email = profile_data.get("email") or f"{account_name}@users.noreply.github.com"
            elif prov == "microsoft":
                account_email = profile_data.get("mail") or profile_data.get("userPrincipalName", user_email)
                account_name = profile_data.get("displayName", user_name)
    except Exception as e:
        print(f"Figyelmeztetés: Nem sikerült a profilt lekérni ({prov}): {e}")

    creds = {
        "auth_type": "oauth2",
        "provider": prov,
        "is_sandbox": False,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": token_json.get("token_type", "Bearer"),
        "expires_in": expires_in,
        "expires_at": expires_at,
        "scopes": token_json.get("scope", spec["default_scopes"]),
        "account_email": account_email,
        "account_name": account_name,
        "connected_at": now.isoformat()
    }

    # Mentés a Vaultba
    integration_id = save_user_integration(
        user_id=user_id,
        service_type=prov,
        service_name=f"{spec['name']} ({account_email})",
        credentials=creds,
        status="connected",
        notes=f"Éles OAuth 2.0 csatlakoztatva: {now.strftime('%Y-%m-%d %H:%M')}"
    )

    return {
        "status": "success",
        "integration_id": integration_id,
        "provider": prov,
        "account_email": account_email,
        "credentials": creds,
        "message": f"'{spec['name']}' sikeresen és biztonságosan csatlakoztatva OAuth 2.0-val!"
    }

def refresh_oauth_token(provider: str, refresh_token: str) -> Dict[str, Any]:
    prov = provider.lower()
    spec = get_provider_details(prov)
    if not spec:
        raise ValueError(f"Ismeretlen OAuth szolgáltató: '{provider}'")

    config = get_oauth_app_config(prov)
    client_id = config.get("client_id", "") if config else ""
    client_secret = config.get("client_secret", "") if config else ""
    sandbox_mode = config.get("sandbox_mode", True) if config else True

    if sandbox_mode or refresh_token.startswith("1//sandbox_") or refresh_token.startswith("sandbox_") or "mock" in client_id.lower() or "test" in client_id.lower() or not (client_id and client_secret):
        now = datetime.now()
        expires_at = (now + timedelta(hours=1)).isoformat()
        return {
            "access_token": f"sandbox_refreshed_{secrets.token_hex(16)}",
            "expires_in": 3600,
            "expires_at": expires_at,
            "token_type": "Bearer"
        }

    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = urllib.parse.urlencode(token_payload).encode("utf-8")
    req = urllib.request.Request(spec["token_url"], data=data, headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        resp_data = resp.read().decode("utf-8")
        token_json = json.loads(resp_data)

    access_token = token_json.get("access_token")
    if not access_token:
        raise ValueError("Nem sikerült megújítani az OAuth tokent.")

    expires_in = int(token_json.get("expires_in", 3600))
    now = datetime.now()
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "expires_at": (now + timedelta(seconds=expires_in)).isoformat(),
        "token_type": token_json.get("token_type", "Bearer")
    }

