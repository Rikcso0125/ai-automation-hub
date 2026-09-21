# -*- coding: utf-8 -*-
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import os
import shutil

if os.environ.get("VERCEL"):
    DB_PATH = Path("/tmp") / "hub_data.db"
    orig_db = Path(__file__).resolve().parent.parent / "data" / "hub_data.db"
    if orig_db.exists() and not DB_PATH.exists():
        try:
            shutil.copy2(orig_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hub_data.db"

def init_db():
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    input_payload TEXT,
                    output_payload TEXT,
                    error_message TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS module_configs (
                    module_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    phone TEXT,
                    role TEXT NOT NULL DEFAULT 'client',
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS integrations_vault (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    service_type TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    credentials_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'connected',
                    notes TEXT,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_module_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    module_id TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, module_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oauth_apps_config (
                    provider TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL DEFAULT '',
                    client_secret TEXT NOT NULL DEFAULT '',
                    scopes TEXT NOT NULL DEFAULT '',
                    sandbox_mode INTEGER DEFAULT 1,
                    is_enabled INTEGER DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oauth_states (
                    state TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    redirect_uri TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            # Seed default OAuth apps if empty
            cursor.execute("SELECT COUNT(*) FROM oauth_apps_config")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now().isoformat()
                default_apps = [
                    ("google", "", "", "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/drive.file email profile", 1, 1, now_str),
                    ("github", "", "", "repo,workflow,read:user,user:email", 1, 1, now_str),
                    ("microsoft", "", "", "offline_access Mail.ReadWrite Calendars.ReadWrite User.Read", 1, 1, now_str),
                    ("meta", "", "", "whatsapp_business_messaging,whatsapp_business_management,pages_manage_posts", 1, 1, now_str),
                    ("slack", "", "", "channels:read,chat:write,commands,incoming-webhook", 1, 1, now_str),
                ]
                cursor.executemany("""
                    INSERT INTO oauth_apps_config (provider, client_id, client_secret, scopes, sandbox_mode, is_enabled, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, default_apps)

            conn.commit()
    except Exception as e:
        print(f"Warning: could not init_db: {e}")

init_db()

# --- Password & Security Helpers ---
import hashlib
import secrets
import hmac
import base64
from datetime import timedelta

SESSION_SECRET_KEY = os.environ.get(
    "HUB_SESSION_SECRET",
    "ai-automation-hub-2026-production-hmac-sha256-secret-secure-key"
).encode("utf-8")

def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pwd_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(pwd_hash, stored_hash)

# --- User Management ---
def create_user(email: str, password: str, full_name: str, company_name: str, phone: str = "", role: str = "client") -> Dict[str, Any]:
    email = email.lower().strip()
    full_name = full_name.strip()
    company_name = company_name.strip()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError(f"Ezzel az email címmel ('{email}') már regisztráltak!")

        pwd_hash, salt = hash_password(password)
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (email, password_hash, salt, full_name, company_name, phone, role, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, pwd_hash, salt, full_name, company_name, phone, role, now, now))
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "company_name": company_name,
            "phone": phone,
            "role": role
        }

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    email = email.lower().strip()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return None

        if verify_password(password, row["password_hash"], row["salt"]):
            now = datetime.now().isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
            conn.commit()
            return {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "company_name": row["company_name"],
                "phone": row["phone"],
                "role": row["role"],
                "created_at": row["created_at"],
                "last_login": now
            }
        return None

def create_session(user_id: int, duration_days: int = 30) -> str:
    user = get_client_by_id(user_id) or {}
    now = datetime.now()
    exp_ts = int((now + timedelta(days=duration_days)).timestamp())
    expires_at = (now + timedelta(days=duration_days)).isoformat()

    # 1. Stateless HMAC-SHA256 Token generálás (Vercel Serverless független)
    payload = {
        "uid": user_id,
        "email": user.get("email", ""),
        "role": user.get("role", "client"),
        "name": user.get("full_name", ""),
        "company": user.get("company_name", ""),
        "exp": exp_ts,
        "rnd": secrets.token_hex(6)
    }
    p_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    p_b64 = base64.urlsafe_b64encode(p_bytes).decode("utf-8").rstrip("=")
    sig = hmac.new(SESSION_SECRET_KEY, p_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    signed_token = f"{p_b64}.{sig}"

    # 2. Helyi adatbázisba mentés (audit és munkamenet követés)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (signed_token, user_id, now.isoformat(), expires_at))
            conn.commit()
    except Exception as e:
        print(f"create_session DB note: {e}")

    return signed_token

def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None

    # 1. Stateless HMAC-SHA256 Token Érvényesítés
    if "." in token:
        try:
            parts = token.split(".", 1)
            if len(parts) == 2:
                p_b64, sig = parts
                expected_sig = hmac.new(SESSION_SECRET_KEY, p_b64.encode("utf-8"), hashlib.sha256).hexdigest()
                if secrets.compare_digest(sig, expected_sig):
                    padded_b64 = p_b64 + "=" * ((4 - len(p_b64) % 4) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(padded_b64.encode("utf-8")).decode("utf-8"))
                    now_ts = datetime.now().timestamp()
                    if payload.get("exp", 0) > now_ts:
                        uid = payload["uid"]
                        user = get_client_by_id(uid)
                        if user:
                            return user

                        # Ha a serverless lambda új konténer és a DB még üres,
                        # automatikusan helyreállítjuk a felhasználót az SQLite-ban:
                        email = payload.get("email", "").lower().strip()
                        if email:
                            with sqlite3.connect(DB_PATH) as conn:
                                conn.row_factory = sqlite3.Row
                                cursor = conn.cursor()
                                cursor.execute("SELECT id, email, full_name, company_name, phone, role, created_at, last_login FROM users WHERE email = ?", (email,))
                                row = cursor.fetchone()
                                if row:
                                    return dict(row)

                                dummy_pwd, dummy_salt = hash_password(secrets.token_hex(16))
                                now_iso = datetime.now().isoformat()
                                cursor.execute("""
                                    INSERT OR IGNORE INTO users (id, email, password_hash, salt, full_name, company_name, phone, role, created_at, last_login)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (uid, email, dummy_pwd, dummy_salt, payload.get("name", "Felhasználó"), payload.get("company", "Vállalkozás"), "", payload.get("role", "client"), now_iso, now_iso))
                                conn.commit()

                        return {
                            "id": uid,
                            "email": payload.get("email", ""),
                            "full_name": payload.get("name", "Felhasználó"),
                            "company_name": payload.get("company", "Vállalkozás"),
                            "phone": "",
                            "role": payload.get("role", "client"),
                            "created_at": datetime.now().isoformat(),
                            "last_login": datetime.now().isoformat()
                        }
        except Exception as ex:
            print(f"Stateless session decode note: {ex}")

    # 2. Hagyományos / Visszafelé kompatibilis SQLite session keresés
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.email, u.full_name, u.company_name, u.phone, u.role, u.created_at, u.last_login
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > ?
            """, (token, datetime.now().isoformat()))
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception as e:
        print(f"DB session lookup note: {e}")

    return None

def delete_session(token: str):
    if not token:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        conn.commit()

def list_all_clients() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.company_name, u.phone, u.role, u.created_at, u.last_login,
                   (SELECT COUNT(*) FROM integrations_vault iv WHERE iv.user_id = u.id) AS integration_count,
                   (SELECT COUNT(*) FROM tenant_module_configs tmc WHERE tmc.user_id = u.id AND tmc.is_active = 1) AS active_modules_count
            FROM users u
            ORDER BY u.id DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_client_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, company_name, phone, role, created_at, last_login
            FROM users WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Integrations Vault (Client Third-party Credentials) ---
def save_user_integration(user_id: int, service_type: str, service_name: str,
                          credentials: Dict[str, Any], status: str = "connected", notes: str = "") -> int:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Check if service of this type already exists for user
        cursor.execute("""
            SELECT id FROM integrations_vault
            WHERE user_id = ? AND service_type = ?
        """, (user_id, service_type))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE integrations_vault
                SET service_name = ?, credentials_json = ?, status = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """, (service_name, json.dumps(credentials, ensure_ascii=False), status, notes, now, row[0]))
            conn.commit()
            return row[0]
        else:
            cursor.execute("""
                INSERT INTO integrations_vault (user_id, service_type, service_name, credentials_json, status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, service_type, service_name, json.dumps(credentials, ensure_ascii=False), status, notes, now))
            conn.commit()
            return cursor.lastrowid

def get_user_integrations(user_id: int, hide_secrets: bool = False) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM integrations_vault
            WHERE user_id = ?
            ORDER BY id ASC
        """, (user_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            creds = json.loads(r["credentials_json"]) if r["credentials_json"] else {}
            if hide_secrets:
                masked_creds = {}
                secret_keywords = {"token", "secret", "password", "key"}
                for k, v in creds.items():
                    is_secret = any(sk in k.lower() for sk in secret_keywords)
                    if is_secret:
                        if isinstance(v, str) and len(v) > 6:
                            masked_creds[k] = v[:3] + "..." + v[-3:]
                        else:
                            masked_creds[k] = "******"
                    else:
                        masked_creds[k] = v
                creds = masked_creds
            result.append({
                "id": r["id"],
                "service_type": r["service_type"],
                "service_name": r["service_name"],
                "credentials": creds,
                "status": r["status"],
                "notes": r["notes"],
                "updated_at": r["updated_at"]
            })
        return result

def delete_user_integration(user_id: int, integration_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM integrations_vault WHERE id = ? AND user_id = ?", (integration_id, user_id))
        conn.commit()

# --- Seed Default Users & Demo Integrations (Szuper Admin + Teszt Ügyfél) ---
def seed_default_users():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # 1. Szuper Admin fiók ellenőrzése / létrehozása
            cursor.execute("SELECT id FROM users WHERE email = 'admin@automationhub.ai'")
            if not cursor.fetchone():
                create_user(
                    email="admin@automationhub.ai",
                    password="Admin2026!Secure",
                    full_name="Központi Rendszergazda",
                    company_name="AI Automation Hub HQ",
                    phone="+36301234567",
                    role="superadmin"
                )
                print(">>> Default Super Admin created: admin@automationhub.ai (Password: Admin2026!Secure)")

            # 2. Példa Ügyfél (János Kovács) fiók ellenőrzése / létrehozása
            cursor.execute("SELECT id FROM users WHERE email = 'janos.kovacs@kovacskft.hu'")
            row_client = cursor.fetchone()
            if not row_client:
                client = create_user(
                    email="janos.kovacs@kovacskft.hu",
                    password="TitkosJelszo2026!",
                    full_name="Kovács János",
                    company_name="Kovács Épületgépészet Kft.",
                    phone="+36309876543",
                    role="client"
                )
                client_id = client["id"]
                print(">>> Default Demo Client created: janos.kovacs@kovacskft.hu (Password: TitkosJelszo2026!)")

                # Minta integrációk rögzítése a teszt ügyfélhez
                save_user_integration(
                    user_id=client_id,
                    service_type="google",
                    service_name="Google Workspace / Gmail (Kovács Kft.)",
                    credentials={
                        "auth_type": "oauth2",
                        "provider": "google",
                        "account_email": "janos.kovacs@kovacskft.hu",
                        "account_name": "Kovács János",
                        "is_sandbox": True,
                        "scopes": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar",
                        "access_token": "sandbox_token_google_demo123",
                        "refresh_token": "1//sandbox_refresh_google_demo123"
                    },
                    status="connected",
                    notes="Hivatalos Gmail és Google Naptár OAuth 2.0 kapcsolat"
                )
                save_user_integration(
                    user_id=client_id,
                    service_type="szamlazz",
                    service_name="Számlázz.hu Agent Kapcsolat",
                    credentials={
                        "agent_key": "szamlazz_agent_kovacs_kft_demo_key_2026"
                    },
                    status="connected",
                    notes="Elektronikus számla és díjbekérő automatikus kiállítás"
                )
    except Exception as e:
        print(f"seed_default_users notice: {e}")

seed_default_users()

# --- Tenant Module Configurations ---
def save_tenant_module_config(user_id: int, module_id: str, config: Dict[str, Any], is_active: bool = True):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tenant_module_configs (user_id, module_id, config_json, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, module_id) DO UPDATE SET
                config_json = excluded.config_json,
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
        """, (user_id, module_id, json.dumps(config, ensure_ascii=False), 1 if is_active else 0, now))
        conn.commit()

def get_tenant_module_config(user_id: int, module_id: str) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT config_json, is_active FROM tenant_module_configs
            WHERE user_id = ? AND module_id = ?
        """, (user_id, module_id))
        row = cursor.fetchone()
        if row:
            cfg = json.loads(row["config_json"])
            cfg["_is_active"] = bool(row["is_active"])
            return cfg
        return {}

def log_execution(module_id: str, status: str, duration_ms: int,
                  input_payload: Any, output_payload: Any, error_message: Optional[str] = None) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO execution_logs 
            (timestamp, module_id, status, duration_ms, input_payload, output_payload, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            module_id,
            status,
            duration_ms,
            json.dumps(input_payload, ensure_ascii=False) if input_payload else None,
            json.dumps(output_payload, ensure_ascii=False) if output_payload else None,
            error_message
        ))
        conn.commit()
        return cursor.lastrowid

def get_recent_logs(limit: int = 50, module_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if module_id:
            cursor.execute("""
                SELECT * FROM execution_logs 
                WHERE module_id = ? 
                ORDER BY id DESC LIMIT ?
            """, (module_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM execution_logs 
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "module_id": r["module_id"],
                "status": r["status"],
                "duration_ms": r["duration_ms"],
                "input_payload": json.loads(r["input_payload"]) if r["input_payload"] else {},
                "output_payload": json.loads(r["output_payload"]) if r["output_payload"] else {},
                "error_message": r["error_message"]
            })
        return logs

def save_module_config(module_id: str, config: Dict[str, Any], is_active: bool = True):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO module_configs (module_id, config_json, is_active, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(module_id) DO UPDATE SET
                config_json = excluded.config_json,
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
        """, (module_id, json.dumps(config, ensure_ascii=False), 1 if is_active else 0, now))
        conn.commit()

def get_module_config(module_id: str) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT config_json, is_active FROM module_configs WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        if row:
            cfg = json.loads(row["config_json"])
            cfg["_is_active"] = bool(row["is_active"])
            return cfg
        return {"_is_active": True}

def get_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM execution_logs")
        total_runs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE status = 'success'")
        successful_runs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE status = 'error'")
        failed_runs = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM execution_logs WHERE timestamp LIKE ?", (f"{today}%",))
        runs_today = cursor.fetchone()[0]

        success_rate = round((successful_runs / total_runs * 100), 1) if total_runs > 0 else 100.0

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "runs_today": runs_today,
            "success_rate": success_rate
        }

# --- OAuth 2.0 System Database Helpers ---
def save_oauth_app_config(provider: str, client_id: str, client_secret: str, scopes: str = "", sandbox_mode: bool = True, is_enabled: bool = True) -> None:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO oauth_apps_config (provider, client_id, client_secret, scopes, sandbox_mode, is_enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                client_id = excluded.client_id,
                client_secret = excluded.client_secret,
                scopes = excluded.scopes,
                sandbox_mode = excluded.sandbox_mode,
                is_enabled = excluded.is_enabled,
                updated_at = excluded.updated_at
        """, (provider, client_id, client_secret, scopes, 1 if sandbox_mode else 0, 1 if is_enabled else 0, now))
        conn.commit()

def get_oauth_app_config(provider: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM oauth_apps_config WHERE provider = ?", (provider,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "provider": row["provider"],
            "client_id": row["client_id"],
            "client_secret": row["client_secret"],
            "scopes": row["scopes"],
            "sandbox_mode": bool(row["sandbox_mode"]),
            "is_enabled": bool(row["is_enabled"]),
            "updated_at": row["updated_at"]
        }

def list_all_oauth_apps_config() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM oauth_apps_config ORDER BY provider")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            sec = r["client_secret"]
            masked_sec = (sec[:4] + "..." + sec[-3:]) if len(sec) > 7 else ("******" if sec else "")
            result.append({
                "provider": r["provider"],
                "client_id": r["client_id"],
                "client_secret_masked": masked_sec,
                "has_secret": bool(sec),
                "scopes": r["scopes"],
                "sandbox_mode": bool(r["sandbox_mode"]),
                "is_enabled": bool(r["is_enabled"]),
                "updated_at": r["updated_at"]
            })
        return result

def create_oauth_state(user_id: int, provider: str, redirect_uri: str) -> str:
    state = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(minutes=15)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO oauth_states (state, user_id, provider, redirect_uri, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (state, user_id, provider, redirect_uri, now.isoformat(), expires.isoformat()))
        conn.commit()
    return state

def verify_and_consume_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM oauth_states WHERE state = ?", (state,))
        row = cursor.fetchone()
        if not row:
            return None
        cursor.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        conn.commit()

        # Check expiry
        now_str = datetime.now().isoformat()
        if row["expires_at"] < now_str:
            return None

        return {
            "state": row["state"],
            "user_id": row["user_id"],
            "provider": row["provider"],
            "redirect_uri": row["redirect_uri"]
        }

def update_vault_credentials(integration_id: int, new_credentials: Dict[str, Any]) -> None:
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE integrations_vault 
            SET credentials_json = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(new_credentials, ensure_ascii=False), now, integration_id))
        conn.commit()
